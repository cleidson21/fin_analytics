import os

router_code = """
import logging
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import List, Dict

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.shared.db import get_db_connection
from backend.domains.investments.engines.valuation_engine import ValuationResult
from backend.domains.investments.engines.wealth_engine import WealthSummary, AssetSummary, InstitutionSummary
from backend.domains.investments.engines.performance_engine import PerformanceEngine
from backend.domains.investments.engines.performance_dto import PerformanceSummary
from backend.domains.investments.import_report import ImportReport
from backend.domains.investments.dto import ReconciliationResult, ImportLogDTO, PerformanceHistory, MessageResponse
from backend.domains.investments.engines.financial_analytics_dto import FinancialPerformanceDTO
from backend.domains.investments.application_factory import ApplicationFactory
from backend.domains.investments.dashboard_dto import PortfolioDashboardDTO, AllocationDashboardDTO, PerformanceDashboardDTO, RiskDashboardDTO, DashboardFullDTO

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Investments"])

def get_dummy_market_prices() -> Dict[str, Decimal]:
    return {}

@router.get(
    "/portfolio", 
    response_model=WealthSummary,
    summary="Obter Consolidação Patrimonial",
    description="Retorna o consolidado patrimonial global do investidor calculado em tempo real.",
    responses={
        200: {"description": "Retorna o WealthSummary completo."},
        500: {"description": "Erro interno nas engines de consolidação."}
    }
)
def get_portfolio(db: Session = Depends(get_db_connection)):
    trade_repo = ApplicationFactory.get_trade_repository()
    from backend.domains.investments.repositories.snapshot_repository import SnapshotRepository
    snapshot_repo = SnapshotRepository()
        
    trades = trade_repo.list_all(db)
    snapshots = snapshot_repo.list_all(db)
    
    portfolio_app = ApplicationFactory.get_portfolio_application_service()
    res = portfolio_app.get_current_portfolio(trades, snapshots, get_dummy_market_prices())
    return res['wealth']


@router.get(
    "/positions", 
    response_model=List[ValuationResult],
    summary="Obter Posições Detalhadas",
    description="Retorna a lista de posições individuais de ativos já com valuation aplicado MTM (Mark-to-Market).",
    responses={
        200: {"description": "Lista de ValuationResults."}
    }
)
def get_positions(db: Session = Depends(get_db_connection)):
    trade_repo = ApplicationFactory.get_trade_repository()
    from backend.domains.investments.repositories.snapshot_repository import SnapshotRepository
    snapshot_repo = SnapshotRepository()
    
    trades = trade_repo.list_all(db)
    snapshots = snapshot_repo.list_all(db)
    
    portfolio_app = ApplicationFactory.get_portfolio_application_service()
    res = portfolio_app.get_current_portfolio(trades, snapshots, get_dummy_market_prices())
    return res['valuations']


@router.get(
    "/performance", 
    response_model=PerformanceSummary,
    summary="Obter Resumo de Performance Simples",
    description="Retorna um resumo não-histórico da performance com base apenas nos saldos do instante (Legado ou Simples)."
)
def get_performance(db: Session = Depends(get_db_connection)):
    wealth = get_portfolio(db)
    perf_engine = PerformanceEngine()
    start_date = date(datetime.now(timezone.utc).year, 1, 1)
    end_date = date.today()
    return perf_engine.calculate(
        cost_basis=wealth.total_cost_basis,
        market_value=wealth.total_market_value,
        realized_gain=Decimal('0'),
        dividends_received=Decimal('0'),
        start_date=start_date,
        end_date=end_date,
        cashflows=[],
        sub_period_returns=[]
    )


@router.get(
    "/performance/history", 
    response_model=PerformanceHistory,
    summary="Gerar Histórico Temporal de Performance",
    description="Aciona o HistoryService para reconstituir o D-0 de cada dia no portfólio."
)
def get_performance_history(db: Session = Depends(get_db_connection)):
    trade_repo = ApplicationFactory.get_trade_repository()
    from backend.domains.investments.repositories.snapshot_repository import SnapshotRepository
    snapshot_repo = SnapshotRepository()
    
    trades = trade_repo.list_all(db)
    snapshots = snapshot_repo.list_all(db)
    if not trades and not snapshots:
        return PerformanceHistory(points=[], summary={})
        
    start_date = min([t.trade_date for t in trades]) if trades else date(datetime.now(timezone.utc).year, 1, 1)
    end_date = date.today()
    
    portfolio_app = ApplicationFactory.get_portfolio_application_service()
    return portfolio_app.generate_historical_performance(
        trades=trades, snapshots=snapshots, market_prices=get_dummy_market_prices(),
        start_date=start_date, end_date=end_date
    )


@router.get(
    "/performance/analytics", 
    response_model=FinancialPerformanceDTO,
    summary="Métricas de Análise Financeira Avançada",
    description="Retorna indicadores (TWR, MWR, Sharpe, Beta) utilizando o motor FinancialAnalyticsEngine."
)
def get_performance_analytics(db: Session = Depends(get_db_connection)):
    history = get_performance_history(db)
    portfolio_app = ApplicationFactory.get_portfolio_application_service()
    return portfolio_app.calculate_advanced_metrics(history)


@router.get(
    "/allocation", 
    response_model=List[AssetSummary],
    summary="Alocação por Ativos",
    description="Mostra como o patrimônio está particionado entre os ativos."
)
def get_allocation(db: Session = Depends(get_db_connection)):
    return get_portfolio(db).by_asset


@router.get(
    "/institutions", 
    response_model=List[InstitutionSummary],
    summary="Alocação por Instituições",
    description="Mostra a alocação consolidada por corretora ou conta de custódia."
)
def get_institutions(db: Session = Depends(get_db_connection)):
    return get_portfolio(db).by_institution


@router.post(
    "/import/cei", 
    response_model=ImportReport,
    summary="Importar Notas/Extratos da CEI/B3",
    description="Aciona o ImportApplicationService para arquivos padronizados CEI."
)
async def import_cei(file: UploadFile = File(...), db: Session = Depends(get_db_connection)):
    content = await file.read()
    import_app = ApplicationFactory.get_import_application_service()
    return import_app.execute_import(db, content, file.filename, "CEI")


@router.post(
    "/import/open-finance", 
    response_model=ImportReport,
    summary="Importar Open Finance ou OFX",
    description="Aciona o ImportApplicationService para arquivos Open Finance ou OFX de bancos."
)
async def import_open_finance(file: UploadFile = File(...), db: Session = Depends(get_db_connection)):
    content = await file.read()
    import_app = ApplicationFactory.get_import_application_service()
    import_type = "OFX" if file.filename.lower().endswith(".ofx") else "OPEN_FINANCE"
    return import_app.execute_import(db, content, file.filename, import_type)


@router.get(
    "/import/history", 
    response_model=List[ImportLogDTO],
    summary="Listar Histórico de Importações",
    description="Lista o audit trail (Ledger) permanente de todas as ingestões realizadas, suportando filtros opcionais."
)
def get_import_history(
    status: str = None,
    parser: str = None,
    checksum: str = None,
    filename: str = None,
    db: Session = Depends(get_db_connection)
):
    repo = ApplicationFactory.get_import_log_repository()
    filters = {}
    if status: filters["status"] = status
    if parser: filters["parser"] = parser
    if checksum: filters["checksum"] = checksum
    if filename: filters["filename"] = filename
    return repo.list_history(db, filters)


@router.get(
    "/import/{log_id}", 
    response_model=ImportLogDTO,
    summary="Detalhes de uma Importação",
    description="Traz os detalhes de um evento de ingestão (ImportLog) pelo seu log_id único.",
    responses={
        404: {"description": "Log não encontrado."}
    }
)
def get_import_log(log_id: str, db: Session = Depends(get_db_connection)):
    repo = ApplicationFactory.get_import_log_repository()
    log = repo.get_by_id(db, log_id)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log não encontrado")
    return log


@router.delete(
    "/import/{log_id}",
    response_model=MessageResponse,
    summary="Remover ou Desfazer Importação",
    description="Deleta o registro de auditoria e (em breve) desencadeia compensações na base real.",
    responses={
        404: {"description": "Log não encontrado para exclusão."}
    }
)
def delete_import_log(log_id: str, db: Session = Depends(get_db_connection)):
    repo = ApplicationFactory.get_import_log_repository()
    if not repo.delete(db, log_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log não encontrado")
    db.commit()
    return MessageResponse(message="Deletado com sucesso")


@router.get(
    "/reconciliation", 
    response_model=List[ReconciliationResult],
    summary="Conciliar Posições (Snapshot vs Ledger)",
    description="Realiza a reconciliação e identifica as divergências na carteira."
)
def get_reconciliation(db: Session = Depends(get_db_connection)):
    import_app = ApplicationFactory.get_import_application_service()
    return import_app.execute_reconciliation(db)


def _get_base_data_for_dashboard(db: Session):
    trade_repo = ApplicationFactory.get_trade_repository()
    from backend.domains.investments.repositories.snapshot_repository import SnapshotRepository
    snapshot_repo = SnapshotRepository()
    
    trades = trade_repo.list_all(db)
    snapshots = snapshot_repo.list_all(db)
    
    return trades, snapshots, {}


@router.get(
    "/dashboard/summary", 
    response_model=PortfolioDashboardDTO,
    summary="Dashboard: Resumo Financeiro",
    description="Retorna o overview de alto nível com métricas essenciais para o topo do Dashboard."
)
def get_dashboard_summary(db: Session = Depends(get_db_connection)):
    trades, snapshots, prices = _get_base_data_for_dashboard(db)
    service = ApplicationFactory.get_portfolio_dashboard_service()
    return service.get_summary_dashboard(trades, snapshots, prices)


@router.get(
    "/dashboard/allocation", 
    response_model=AllocationDashboardDTO,
    summary="Dashboard: Diversificação",
    description="Retorna os cortes analíticos de alocação (Classe, Setor, Instituição)."
)
def get_dashboard_allocation(db: Session = Depends(get_db_connection)):
    trades, snapshots, prices = _get_base_data_for_dashboard(db)
    service = ApplicationFactory.get_portfolio_dashboard_service()
    return service.get_allocation_dashboard(trades, snapshots, prices)


@router.get(
    "/dashboard/performance", 
    response_model=PerformanceDashboardDTO,
    summary="Dashboard: Retornos e Comparação",
    description="Fornece a fatiada de dados relativa à rentabilidade, rolling returns e benchmark."
)
def get_dashboard_performance(db: Session = Depends(get_db_connection)):
    trades, snapshots, prices = _get_base_data_for_dashboard(db)
    service = ApplicationFactory.get_portfolio_dashboard_service()
    return service.get_performance_dashboard(trades, snapshots, prices)


@router.get(
    "/dashboard/risk", 
    response_model=RiskDashboardDTO,
    summary="Dashboard: Avaliação de Risco",
    description="Fornece índices estatísticos que mensuram risco (Drawdown, Volatilidade)."
)
def get_dashboard_risk(db: Session = Depends(get_db_connection)):
    trades, snapshots, prices = _get_base_data_for_dashboard(db)
    service = ApplicationFactory.get_portfolio_dashboard_service()
    return service.get_risk_dashboard(trades, snapshots, prices)


@router.get(
    "/dashboard", 
    response_model=DashboardFullDTO,
    summary="Dashboard Completo (Full Sync)",
    description="Retorna absolutamente todos os painéis e widgets do Dashboard em uma única requisição agrupada."
)
def get_dashboard_full(db: Session = Depends(get_db_connection)):
    trades, snapshots, prices = _get_base_data_for_dashboard(db)
    service = ApplicationFactory.get_portfolio_dashboard_service()
    return DashboardFullDTO(
        summary=service.get_summary_dashboard(trades, snapshots, prices),
        allocation=service.get_allocation_dashboard(trades, snapshots, prices),
        performance=service.get_performance_dashboard(trades, snapshots, prices),
        risk=service.get_risk_dashboard(trades, snapshots, prices)
    )

"""

path = 'backend/domains/investments/router.py'
with open(path, 'w', encoding='utf-8') as f:
    f.write(router_code)

print('Refatorado router.py com OpenAPI docs e padronização!')
