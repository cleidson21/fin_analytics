from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_current_user
from app.core.observability import metrics
import os
import sqlite3
import time

router = APIRouter()

START_TIME = time.time()

def check_db_health(db_path: str):
    if not os.path.exists(db_path):
        return {"status": "error", "message": "File not found"}
        
    size_mb = os.path.getsize(db_path) / (1024 * 1024)
    conn = sqlite3.connect(db_path)
    integrity = conn.execute('PRAGMA integrity_check').fetchone()[0]
    fks = conn.execute('PRAGMA foreign_key_check').fetchall()
    conn.close()
    
    return {
        "size_mb": round(size_mb, 2),
        "integrity_check": integrity,
        "foreign_key_check": "ok" if not fks else f"failed ({len(fks)} violations)"
    }

def verify_admin(current_user: dict = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado"
        )
    role = current_user.get("role", "").upper()
    if role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores"
        )
    return current_user

@router.get("/health")
def get_health(current_user: dict = Depends(verify_admin)):
    from database.config import FINANCIAL_DB_PATH, GOVERNANCE_DB_PATH
    fin_health = check_db_health(str(FINANCIAL_DB_PATH))
    gov_health = check_db_health(str(GOVERNANCE_DB_PATH))

    # SQLite in Python doesn't expose a global active connections counter easily without parsing the OS level fds
    # But we can assume it's stable if the file is accessible

    return {
        "financial_db": fin_health,
        "governance_db": gov_health,
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "active_connections": "managed_by_driver"
    }

@router.get("/performance")
def get_performance(current_user: dict = Depends(verify_admin)):
    snapshot = metrics.get_snapshot()
    return {
        "metrics": {
            "total_queries": snapshot["total_queries"],
            "total_writes": snapshot["total_writes"],
            "total_rollbacks": snapshot["total_rollbacks"],
            "total_staging_promotions": snapshot["total_staging_promotions"],
            "total_staging_rejections": snapshot["total_staging_rejections"],
            "avg_query_duration_ms": snapshot["avg_query_duration_ms"],
            "max_query_duration_ms": snapshot["max_query_duration_ms"]
        },
        "top_slowest_queries": snapshot["top_slowest_queries"]
    }
