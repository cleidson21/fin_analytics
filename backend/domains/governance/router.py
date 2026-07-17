from fastapi import APIRouter
from typing import Dict, Any, List
from datetime import datetime, timezone

router = APIRouter(prefix="/governance", tags=["Governance"])

@router.get("/dashboard")
def get_governance_dashboard() -> Dict[str, Any]:
    return {
        "total_runs": 42,
        "confirmed_runs": 40,
        "pending_runs": 2,
        "lines_inserted": 1500,
        "lines_updated": 300,
        "lines_failed": 5,
        "last_import": datetime.now(timezone.utc).isoformat()
    }

@router.get("/imports")
def list_imports(limit: int = 10) -> Dict[str, Any]:
    return {
        "items": [
            {
                "id": "mock-id-1",
                "source_type": "PIERRE",
                "file_name": "fatura_nubank.csv",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "status": "CONFIRMED",
                "rows_read": 100,
                "rows_inserted": 100,
                "rows_failed": 0
            },
            {
                "id": "mock-id-2",
                "source_type": "MYPROFIT",
                "file_name": "b3_positions.xlsx",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "status": "AWAITING_CONFIRMATION",
                "rows_read": 50,
                "rows_inserted": 48,
                "rows_failed": 2
            }
        ],
        "total": 2
    }

@router.get("/database/summary")
def get_db_summary() -> Dict[str, Any]:
    return {
        "size_mb": 15.4,
        "tables_count": 12,
        "total_rows": 25000,
        "last_backup": datetime.now(timezone.utc).isoformat(),
        "status": "healthy"
    }

@router.get("/database/health")
def get_db_health() -> Dict[str, Any]:
    return {
        "status": "UP",
        "connections": 1,
        "latency_ms": 5
    }

@router.get("/database/tables")
def get_db_tables() -> List[Dict[str, Any]]:
    return [
        {"name": "transactions", "rows": 10000, "size_kb": 2048},
        {"name": "categories", "rows": 50, "size_kb": 128},
        {"name": "merchants", "rows": 200, "size_kb": 256}
    ]

@router.get("/database/integrity")
def get_db_integrity() -> Dict[str, Any]:
    return {
        "status": "PASS",
        "foreign_keys_ok": True,
        "orphaned_records": 0,
        "checks": [
            {"name": "PRAGMA integrity_check", "passed": True},
            {"name": "PRAGMA foreign_key_check", "passed": True}
        ]
    }

@router.get("/audit")
def list_audit(status_filter: str = "ALL") -> Dict[str, Any]:
    return {
        "items": [],
        "total": 0
    }

@router.get("/audit/rollbacks")
def list_rollbacks() -> Dict[str, Any]:
    return {
        "items": [],
        "total": 0
    }
