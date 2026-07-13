import os

path = 'backend/domains/investments/router.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

import_str = 'from backend.domains.investments.dashboard_dto import PortfolioDashboardDTO, AllocationDashboardDTO, PerformanceDashboardDTO, RiskDashboardDTO\n'
if 'PortfolioDashboardDTO' not in content:
    content = content.replace('from fastapi import UploadFile, File, Depends, HTTPException', import_str + 'from fastapi import UploadFile, File, Depends, HTTPException')

endpoints = """
def _get_base_data_for_dashboard(db: Session):
    trade_repo = ApplicationFactory.get_trade_repository()
    from backend.domains.investments.repositories.snapshot_repository import SnapshotRepository
    snapshot_repo = SnapshotRepository()
    
    trades = trade_repo.list_all(db)
    snapshots = snapshot_repo.list_all(db)
    
    # We use empty market prices for now
    return trades, snapshots, {}

@router.get("/dashboard/summary", response_model=PortfolioDashboardDTO)
def get_dashboard_summary(db: Session = Depends(get_db_connection)):
    trades, snapshots, prices = _get_base_data_for_dashboard(db)
    service = ApplicationFactory.get_portfolio_dashboard_service()
    return service.get_summary_dashboard(trades, snapshots, prices)

@router.get("/dashboard/allocation", response_model=AllocationDashboardDTO)
def get_dashboard_allocation(db: Session = Depends(get_db_connection)):
    trades, snapshots, prices = _get_base_data_for_dashboard(db)
    service = ApplicationFactory.get_portfolio_dashboard_service()
    return service.get_allocation_dashboard(trades, snapshots, prices)

@router.get("/dashboard/performance", response_model=PerformanceDashboardDTO)
def get_dashboard_performance(db: Session = Depends(get_db_connection)):
    trades, snapshots, prices = _get_base_data_for_dashboard(db)
    service = ApplicationFactory.get_portfolio_dashboard_service()
    return service.get_performance_dashboard(trades, snapshots, prices)

@router.get("/dashboard/risk", response_model=RiskDashboardDTO)
def get_dashboard_risk(db: Session = Depends(get_db_connection)):
    trades, snapshots, prices = _get_base_data_for_dashboard(db)
    service = ApplicationFactory.get_portfolio_dashboard_service()
    return service.get_risk_dashboard(trades, snapshots, prices)

@router.get("/dashboard")
def get_dashboard_full(db: Session = Depends(get_db_connection)):
    trades, snapshots, prices = _get_base_data_for_dashboard(db)
    service = ApplicationFactory.get_portfolio_dashboard_service()
    return {
        "summary": service.get_summary_dashboard(trades, snapshots, prices),
        "allocation": service.get_allocation_dashboard(trades, snapshots, prices),
        "performance": service.get_performance_dashboard(trades, snapshots, prices),
        "risk": service.get_risk_dashboard(trades, snapshots, prices)
    }
"""
if '/dashboard/summary' not in content:
    content += endpoints

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated Router with Dashboard endpoints')
