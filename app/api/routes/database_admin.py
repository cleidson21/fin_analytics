import os
from fastapi import APIRouter, Depends
from app.api.deps import require_admin

from app.api.schemas.admin import (
    DatabaseSummary, TableStatus, DatabaseHealth, DatabaseIntegrity,
    VacuumEstimate, VacuumResult
)
from app.api.services.financial_service import FinancialService
from app.api.services.governance_service import GovernanceService

router = APIRouter(dependencies=[Depends(require_admin)])

fin_service = FinancialService()
gov_service = GovernanceService()

@router.get("/summary", response_model=DatabaseSummary)
def get_summary():
    summary = {}
    fin_metrics = fin_service.get_admin_metrics()
    summary.update(fin_metrics)
        
    gov_metrics = gov_service.get_admin_metrics()
    summary.update(gov_metrics)
        
    return summary

@router.get("/tables", response_model=list[TableStatus])
def get_tables():
    results = fin_service.get_table_counts() + gov_service.get_table_counts()
                
    return results

@router.get("/health", response_model=DatabaseHealth)
def get_health():
    tables = get_tables()
    table_dict = {t['table_name']: t['status'] for t in tables}
    
    db_status = "OK" if all(s == "OK" for t, s in table_dict.items() if t in ('import_runs', 'transactions')) else "WARNING"
    imports_status = "OK" if table_dict.get('import_runs', 'ERROR') == 'OK' else "ERROR"
    wealth_status = "OK" if table_dict.get('positions', 'ERROR') == 'OK' and table_dict.get('dividends', 'ERROR') == 'OK' else "ERROR"
    staging_status = "OK" if all(s == "OK" for t, s in table_dict.items() if t.startswith('staging')) else "WARNING"

    integrity = get_integrity()
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
    integrity = {'orphan_runs': 0, 'pending_staging': 0, 'duplicate_transactions_suspects': 0}
    
    fin_int = fin_service.get_integrity_metrics()
    gov_int = gov_service.get_integrity_metrics()
    
    integrity['duplicate_transactions_suspects'] = fin_int.get('duplicate_transactions_suspects', 0)
    integrity['pending_staging'] = gov_int.get('pending_staging', 0)
    
    orphans = fin_int.get('fin_run_ids', set()) - gov_int.get('gov_run_ids', set())
    integrity['orphan_runs'] = len(orphans)

    return integrity

@router.post("/vacuum/estimate", response_model=VacuumEstimate)
def estimate_vacuum():
    current_size = (os.path.getsize(fin_service.get_database_path()) + os.path.getsize(gov_service.get_database_path())) / 1024
    return {
        "size_current_kb": current_size,
        "estimated_post_vacuum_kb": current_size * 0.9
    }

@router.post("/vacuum", response_model=VacuumResult)
def run_vacuum():
    size_before = (os.path.getsize(fin_service.get_database_path()) + os.path.getsize(gov_service.get_database_path()))
    fin_service.vacuum_database()
    # governance repo doesn't have vacuum method in Adapter right now, but we can do it via sql
    gov_service.vacuum_database()
    size_after = (os.path.getsize(fin_service.get_database_path()) + os.path.getsize(gov_service.get_database_path()))
    return {
        "size_before_kb": size_before / 1024,
        "size_after_kb": size_after / 1024,
        "freed_space_kb": (size_before - size_after) / 1024
    }

@router.post("/recount")
def run_recount():
    fin_service.analyze_database()
    gov_service.analyze_database()
    return {"status": "SUCCESS"}
