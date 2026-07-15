
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
from backend.domains.investments.dto import ReconciliationResult, ImportLogDTO, PerformanceHistory, MessageResponse, PaginatedResponse
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
    response_model=PaginatedResponse[ValuationResult],
    summary="Obter Posições Detalhadas",
    description="Retorna a lista de posições individuais de ativos já com valuation aplicado MTM (Mark-to-Market).",
    responses={
        200: {"description": "Lista de ValuationResults."}
    }
)
def get_positions(db: Session = Depends(get_db_connection), page: int = 1, page_size: int = 50):
    trade_repo = ApplicationFactory.get_trade_repository()
    from backend.domains.investments.repositories.snapshot_repository import SnapshotRepository
    snapshot_repo = SnapshotRepository()
    
    trades = trade_repo.list_all(db)
    snapshots = snapshot_repo.list_all(db)
    
    portfolio_app = ApplicationFactory.get_portfolio_application_service()
    res = portfolio_app.get_current_portfolio(trades, snapshots, get_dummy_market_prices())
    return PaginatedResponse(items=res['valuations'], total=len(res['valuations']), page=page, page_size=page_size)


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
    response_model=PaginatedResponse[AssetSummary],
    summary="Alocação por Ativos",
    description="Mostra como o patrimônio está particionado entre os ativos."
)
def get_allocation(db: Session = Depends(get_db_connection), page: int = 1, page_size: int = 50):
    items = get_portfolio(db).by_asset
    return PaginatedResponse(items=items, total=len(items), page=page, page_size=page_size)


@router.get(
    "/institutions", 
    response_model=PaginatedResponse[InstitutionSummary],
    summary="Alocação por Instituições",
    description="Mostra a alocação consolidada por corretora ou conta de custódia."
)
def get_institutions(db: Session = Depends(get_db_connection), page: int = 1, page_size: int = 50):
    items = get_portfolio(db).by_institution
    return PaginatedResponse(items=items, total=len(items), page=page, page_size=page_size)


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
    response_model=PaginatedResponse[ImportLogDTO],
    summary="Listar Histórico de Importações",
    description="Lista o audit trail (Ledger) permanente de todas as ingestões realizadas, suportando filtros opcionais."
)
def get_import_history(
    status: str = None,
    parser: str = None,
    checksum: str = None,
    filename: str = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db_connection)
):
    repo = ApplicationFactory.get_import_log_repository()
    filters = {}
    if status: filters["status"] = status
    if parser: filters["parser"] = parser
    if checksum: filters["checksum"] = checksum
    if filename: filters["filename"] = filename
    items = repo.list_history(db, filters)
    return PaginatedResponse(items=items, total=len(items), page=page, page_size=page_size)


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
    response_model=PaginatedResponse[ReconciliationResult],
    summary="Conciliar Posições (Snapshot vs Ledger)",
    description="Realiza a reconciliação e identifica as divergências na carteira."
)
def get_reconciliation(db: Session = Depends(get_db_connection), page: int = 1, page_size: int = 50):
    import_app = ApplicationFactory.get_import_application_service()
    items = import_app.execute_reconciliation(db)
    return PaginatedResponse(items=items, total=len(items), page=page, page_size=page_size)


def _get_base_data_for_dashboard(db: Session):
    # TSK-7.R2: We no longer need to fetch ALL trades and snapshots for the dashboard
    # The dashboard service will now query the materialized tables directly via SQL.
    # Returning empty lists to satisfy the legacy interface contract.
    return [], [], {}


@router.get(
    "/dashboard/summary", 
    response_model=PortfolioDashboardDTO,
    summary="Dashboard: Resumo Financeiro",
    description="Retorna o overview de alto nível com métricas essenciais para o topo do Dashboard."
)
def get_dashboard_summary(db: Session = Depends(get_db_connection)):
    trades, snapshots, prices = _get_base_data_for_dashboard(db)
    service = ApplicationFactory.get_portfolio_dashboard_service()
    return service.get_summary_dashboard(trades, snapshots, prices, session=db)


@router.get(
    "/dashboard/allocation", 
    response_model=AllocationDashboardDTO,
    summary="Dashboard: Diversificação",
    description="Retorna os cortes analíticos de alocação (Classe, Setor, Instituição)."
)
def get_dashboard_allocation(db: Session = Depends(get_db_connection)):
    trades, snapshots, prices = _get_base_data_for_dashboard(db)
    service = ApplicationFactory.get_portfolio_dashboard_service()
    return service.get_allocation_dashboard(trades, snapshots, prices, session=db)


@router.get(
    "/dashboard/performance", 
    response_model=PerformanceDashboardDTO,
    summary="Dashboard: Retornos e Comparação",
    description="Fornece a fatiada de dados relativa à rentabilidade, rolling returns e benchmark."
)
def get_dashboard_performance(db: Session = Depends(get_db_connection)):
    trades, snapshots, prices = _get_base_data_for_dashboard(db)
    service = ApplicationFactory.get_portfolio_dashboard_service()
    return service.get_performance_dashboard(trades, snapshots, prices, session=db)


@router.get(
    "/dashboard/risk", 
    response_model=RiskDashboardDTO,
    summary="Dashboard: Avaliação de Risco",
    description="Fornece índices estatísticos que mensuram risco (Drawdown, Volatilidade)."
)
def get_dashboard_risk(db: Session = Depends(get_db_connection)):
    trades, snapshots, prices = _get_base_data_for_dashboard(db)
    service = ApplicationFactory.get_portfolio_dashboard_service()
    return service.get_risk_dashboard(trades, snapshots, prices, session=db)


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
        summary=service.get_summary_dashboard(trades, snapshots, prices, session=db),
        allocation=service.get_allocation_dashboard(trades, snapshots, prices, session=db),
        performance=service.get_performance_dashboard(trades, snapshots, prices, session=db),
        risk=service.get_risk_dashboard(trades, snapshots, prices, session=db)
    )

# --- ENDPOINTS FALTANTES FASE 7 (TSK-7.R3) ---

from backend.domains.investments.dto import PortfolioEvolutionSummary, DividendHistoryDTO, DividendBreakdownDTO
from sqlalchemy import text

@router.get("/evolution/summary", response_model=PortfolioEvolutionSummary)
def get_evolution_summary(db: Session = Depends(get_db_connection)):
    query = text("""
        SELECT total_equity, cost_basis, cumulative_twr, dividends_total
        FROM portfolio_snapshots 
        ORDER BY date DESC LIMIT 1
    """)
    row = db.execute(query).fetchone()
    if not row:
        return PortfolioEvolutionSummary(
            current_wealth=Decimal('0'), total_invested=Decimal('0'),
            total_dividends=Decimal('0'), accumulated_return_pct=Decimal('0')
        )
    return PortfolioEvolutionSummary(
        current_wealth=Decimal(str(row.total_equity or 0))/100,
        total_invested=Decimal(str(row.cost_basis or 0))/100,
        total_dividends=Decimal(str(row.dividends_total or 0))/100,
        accumulated_return_pct=Decimal(str((row.cumulative_twr or 0) * 100))
    )

@router.get("/evolution/history")
def get_evolution_history(db: Session = Depends(get_db_connection)):
    return get_performance_history(db).points

@router.get("/dividends/history", response_model=List[DividendHistoryDTO])
def get_dividends_history(db: Session = Depends(get_db_connection)):
    query = text("""
        SELECT d.id, a.ticker, d.type, d.gross_amount, d.payment_date 
        FROM dividends d
        JOIN assets a ON d.asset_id = a.id
        ORDER BY d.payment_date DESC
    """)
    rows = db.execute(query).fetchall()
    return [
        DividendHistoryDTO(
            id_economico=r.id,
            ticker=r.ticker,
            tipo_evento=r.type,
            valor=Decimal(str(r.gross_amount))/100,
            data_pagamento=str(r.payment_date) if r.payment_date else None,
            observacao=None
        )
        for r in rows
    ]

@router.get("/dividends/breakdown", response_model=List[DividendBreakdownDTO])
def get_dividends_breakdown(db: Session = Depends(get_db_connection)):
    query = text("""
        SELECT a.ticker, SUM(d.gross_amount) as total
        FROM dividends d
        JOIN assets a ON d.asset_id = a.id
        GROUP BY a.ticker
        ORDER BY total DESC
    """)
    rows = db.execute(query).fetchall()
    return [
        DividendBreakdownDTO(
            ticker=r.ticker,
            total_received=Decimal(str(r.total or 0))/100
        )
        for r in rows
    ]

@router.get("/asset/{ticker}")
def get_asset_detail(ticker: str, db: Session = Depends(get_db_connection)):
    pos_query = text("""
        SELECT a.ticker, a.asset_class, v.last_price, v.market_value, v.unrealized_gain, v.portfolio_weight
        FROM asset_valuations v
        JOIN assets a ON v.asset_id = a.id
        WHERE a.ticker = :ticker 
        ORDER BY v.price_date DESC LIMIT 1
    """)
    pos_row = db.execute(pos_query, {"ticker": ticker}).fetchone()
    
    pos_data = {
        "ticker": ticker,
        "quantidade": 0,
        "preco_medio": 0,
        "valor_investido": 0,
        "preco_atual": 0,
        "valor_atual": 0,
        "ganho": 0,
        "asset_class": "OUTROS",
        "asset_subclass": "",
        "peso": 0
    }
    
    if pos_row:
        mv = float(pos_row.market_value or 0) / 100
        ug = float(pos_row.unrealized_gain or 0) / 100
        lp = float(pos_row.last_price or 0) / 100
        
        cb = mv - ug
        qty = mv / lp if lp > 0 else 0
        avg_price = cb / qty if qty > 0 else 0
        
        pos_data.update({
            "quantidade": qty,
            "preco_medio": avg_price,
            "valor_investido": cb,
            "preco_atual": lp,
            "valor_atual": mv,
            "ganho": ug,
            "asset_class": pos_row.asset_class or "OUTROS",
            "peso": float(pos_row.portfolio_weight or 0)
        })

    div_query = text("""
        SELECT type, gross_amount, payment_date 
        FROM dividends d
        JOIN assets a ON d.asset_id = a.id
        WHERE a.ticker = :ticker
        ORDER BY payment_date DESC
    """)
    div_rows = db.execute(div_query, {"ticker": ticker}).fetchall()
    
    div_items = []
    tot_divs = 0
    for r in div_rows:
        val = float(r.gross_amount or 0) / 100
        tot_divs += val
        div_items.append({
            "tipo_evento": r.type,
            "valor": val,
            "data_pagamento": str(r.payment_date)
        })

    return {
        "position": pos_data,
        "market_data": { "available": False, "history": [] },
        "indicators": { "available": False, "indicators": {} },
        "dividends": { 
            "items": div_items, 
            "kpis": { 
                "total": tot_divs, 
                "last_12m": tot_divs, 
                "yoc": (tot_divs / pos_data["valor_investido"]) if pos_data["valor_investido"] > 0 else 0 
            } 
        },
        "timeline": []
    }
