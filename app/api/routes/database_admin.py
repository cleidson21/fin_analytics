import os
from fastapi import APIRouter, Depends
from app.api.deps import require_admin

from app.api.schemas.admin import (
    DatabaseSummary, TableStatus, DatabaseHealth, DatabaseIntegrity,
    VacuumEstimate, VacuumResult, AuditRun, AuditRollback
)
from database.repository import DatabaseManager
from database.queries import FinancialQueries

router = APIRouter(dependencies=[Depends(require_admin)])
repository = DatabaseManager()
queries = FinancialQueries()

@router.get("/summary", response_model=DatabaseSummary)
def get_summary():
    return queries.get_database_summary()

@router.get("/tables", response_model=list[TableStatus])
def get_tables():
    return queries.get_database_tables()

@router.get("/health", response_model=DatabaseHealth)
def get_health():
    # Health check depends on tables sizes and constraints
    tables = queries.get_database_tables()
    table_dict = {t['table_name']: t['status'] for t in tables}
    
    db_status = "OK" if all(s == "OK" for t, s in table_dict.items() if t in ('import_runs', 'transactions')) else "WARNING"
    imports_status = "OK" if table_dict.get('import_runs', 'ERROR') == 'OK' else "ERROR"
    wealth_status = "OK" if table_dict.get('positions', 'ERROR') == 'OK' and table_dict.get('dividends', 'ERROR') == 'OK' else "ERROR"
    staging_status = "OK" if all(s == "OK" for t, s in table_dict.items() if t.startswith('staging')) else "WARNING"

    integrity = queries.get_database_integrity()
    if integrity['orphan_runs'] > 0 or integrity['duplicate_transactions_suspects'] > 0:
        db_status = "WARNING"

    return {
        "database": db_status,
        "imports": imports_status,
        "wealth": wealth_status,
        "staging": staging_status
    }

@router.get("/integrity", response_model=DatabaseIntegrity)
def get_integrity():
    return queries.get_database_integrity()

@router.post("/vacuum/estimate", response_model=VacuumEstimate)
def estimate_vacuum():
    current_size = os.path.getsize(repository.db_path) / 1024
    # VACUUM doesn't guarantee a percentage reduction, but typically 5-20% depending on deleted rows.
    # We provide a dummy estimate here just to show user an estimate and current size.
    return {
        "size_current_kb": current_size,
        "estimated_post_vacuum_kb": current_size * 0.9
    }

@router.post("/vacuum", response_model=VacuumResult)
def run_vacuum():
    res = repository.vacuum_database()
    return {
        "size_before_kb": res["size_before_bytes"] / 1024,
        "size_after_kb": res["size_after_bytes"] / 1024,
        "freed_space_kb": (res["size_before_bytes"] - res["size_after_bytes"]) / 1024
    }

@router.post("/recount")
def run_recount():
    success = repository.analyze_database()
    return {"status": "SUCCESS" if success else "ERROR"}

