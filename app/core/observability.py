import threading
import logging
from datetime import datetime
import json

class MetricsRegistry:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MetricsRegistry, cls).__new__(cls)
                cls._instance._init_metrics()
        return cls._instance

    def _init_metrics(self):
        self.total_queries = 0
        self.total_writes = 0
        self.total_rollbacks = 0
        self.total_staging_promotions = 0
        self.total_staging_rejections = 0
        self.cumulative_query_time = 0.0
        self.max_query_duration_ms = 0.0
        self.top_slowest_queries = []  # List of dicts: {'query': str, 'duration_ms': float}
        self._metric_lock = threading.Lock()

    def record_query(self, duration_ms: float, query_name: str, is_write: bool = False):
        with self._metric_lock:
            self.total_queries += 1
            if is_write:
                self.total_writes += 1
            
            self.cumulative_query_time += duration_ms
            
            if duration_ms > self.max_query_duration_ms:
                self.max_query_duration_ms = duration_ms

            # Maintain top 50 slowest queries
            self.top_slowest_queries.append({'query': query_name, 'duration_ms': duration_ms})
            self.top_slowest_queries.sort(key=lambda x: x['duration_ms'], reverse=True)
            if len(self.top_slowest_queries) > 50:
                self.top_slowest_queries = self.top_slowest_queries[:50]

    def record_rollback(self):
        with self._metric_lock:
            self.total_rollbacks += 1

    def record_staging_promotion(self):
        with self._metric_lock:
            self.total_staging_promotions += 1

    def record_staging_rejection(self):
        with self._metric_lock:
            self.total_staging_rejections += 1

    @property
    def avg_query_duration_ms(self) -> float:
        with self._metric_lock:
            if self.total_queries == 0:
                return 0.0
            return self.cumulative_query_time / self.total_queries

    def get_snapshot(self):
        with self._metric_lock:
            return {
                "total_queries": self.total_queries,
                "total_writes": self.total_writes,
                "total_rollbacks": self.total_rollbacks,
                "total_staging_promotions": self.total_staging_promotions,
                "total_staging_rejections": self.total_staging_rejections,
                "avg_query_duration_ms": round(self.avg_query_duration_ms, 2),
                "max_query_duration_ms": round(self.max_query_duration_ms, 2),
                "top_slowest_queries": self.top_slowest_queries.copy()
            }


class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def log_request(self, request_id: str, service: str, repository: str, endpoint: str, duration_ms: float, status_code: int, **kwargs):
        # Prevent logging sensitive fields
        sensitive_keys = ['token', 'password', 'hash', 'payload']
        safe_kwargs = {}
        for k, v in kwargs.items():
            if any(s in k.lower() for s in sensitive_keys):
                safe_kwargs[k] = '***OBFUSCATED***'
            else:
                safe_kwargs[k] = v

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        log_parts = [
            f"[{timestamp}]",
            f"request_id={request_id}",
            f"service={service}",
            f"repository={repository}",
            f"endpoint={endpoint}",
            f"duration_ms={duration_ms:.2f}",
            f"status={status_code}"
        ]
        
        for k, v in safe_kwargs.items():
            log_parts.append(f"{k}={v}")
            
        self.logger.info(" ".join(log_parts))

metrics = MetricsRegistry()

from contextlib import contextmanager
import time
import uuid

@contextmanager
def transaction_scope(conn, operation_name: str):
    conn.isolation_level = None  # Disable autocommit
    conn.execute('BEGIN')
    t0 = time.time()
    try:
        yield conn
        conn.execute('COMMIT')
        duration_ms = (time.time() - t0) * 1000
        metrics.record_query(duration_ms, operation_name, is_write=True)
    except Exception as e:
        conn.execute('ROLLBACK')
        metrics.record_rollback()
        raise e
    finally:
        conn.isolation_level = '' # Restore autocommit

@contextmanager
def query_scope(conn, operation_name: str):
    t0 = time.time()
    try:
        yield conn
    finally:
        duration_ms = (time.time() - t0) * 1000
        metrics.record_query(duration_ms, operation_name, is_write=False)
