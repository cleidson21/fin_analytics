from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from backend.api.dependencies.legacy_financial import require_certified_legacy_financial_scope
from backend.application.services.local_ledger_scope import CertifiedLedgerScope, LedgerScopeDenied
from backend.domains.pierre.pipeline import PierreImportPipeline

from backend.api.dependencies.auth import get_current_user
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.application.dtos.transaction import CategoryBreakdownDTO
from backend.application.dtos.sync_result_dto import SyncResultDTO

# GovernedFinancialQuery e SessionLocal importados de forma lazy
# (dentro de cada endpoint) para evitar conflito de MetaData no reload do uvicorn.

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _current_month() -> str:
    today = date.today()
    return f"{today.year}-{today.month:02d}"


@router.get("/summary-v2")
def get_dashboard_summary_v2(
    month: str = Query(None, description="YYYY-MM"),
    current_user: UserResponseDTO = Depends(get_current_user),
    scope: CertifiedLedgerScope = Depends(require_certified_legacy_financial_scope),
):
    """
    KPIs do Dashboard: receitas, despesas, saldo_líquido, patrimônio.

    Usa somente transações CLASSIFIED da camada Pierre/governança.
    Retorna variação percentual vs mês anterior.
    """
    if not month:
        month = _current_month()

    from backend.domains.pierre.repository import GovernedFinancialQuery
    q = GovernedFinancialQuery()
    db = scope.db
    try:
        result = q.get_monthly_kpis(db, month=month)
        db.expunge_all()
    finally:
        db.close()
    return result


@router.get("/pacing-v2")
def get_dashboard_pacing_v2(
    month: str = Query(None, description="YYYY-MM"),
    current_user: UserResponseDTO = Depends(get_current_user),
    scope: CertifiedLedgerScope = Depends(require_certified_legacy_financial_scope),
):
    """
    Ritmo de Gastos diário — gráfico de linha mês atual vs mês anterior.

    Retorna gastos (SAIDA CLASSIFIED) dia a dia e totais para comparação.
    """
    if not month:
        month = _current_month()

    from backend.domains.pierre.repository import GovernedFinancialQuery
    q = GovernedFinancialQuery()
    db = scope.db
    try:
        result = q.get_pacing_data(db, month=month)
        db.expunge_all()
    finally:
        db.close()
    return result


@router.get("/heatmap")
def get_dashboard_heatmap(
    month: str = Query(None, description="YYYY-MM"),
    current_user: UserResponseDTO = Depends(get_current_user),
    scope: CertifiedLedgerScope = Depends(require_certified_legacy_financial_scope),
):
    """
    Mapa de Calor de gastos diários.

    Retorna todos os dias do mês com valor total (SAIDA CLASSIFIED)
    e intensidade normalizada 0–1 para coloração do grid.
    """
    if not month:
        month = _current_month()

    from backend.domains.pierre.repository import GovernedFinancialQuery
    q = GovernedFinancialQuery()
    db = scope.db
    try:
        result = q.get_heatmap_data(db, month=month)
        db.expunge_all()
    finally:
        db.close()
    return result


@router.get("/categories", response_model=List[CategoryBreakdownDTO])
def get_categories_summary(
    month: str = Query(None, description="YYYY-MM"),
    current_user: UserResponseDTO = Depends(get_current_user),
    scope: CertifiedLedgerScope = Depends(require_certified_legacy_financial_scope),
):
    """
    Retorna o breakdown de gastos por categoria para o Dashboard e Página de Categorias.
    """
    if not month:
        month = _current_month()

    from backend.domains.pierre.repository import GovernedFinancialQuery
    
    q = GovernedFinancialQuery()
    db = scope.db
    try:
        result = q.get_categories_breakdown(db, month=month)
        db.expunge_all()
    finally:
        db.close()
        
    return result


@router.post("/import-pierre", response_model=SyncResultDTO)
async def import_pierre_data(
    start_date: Optional[date] = Query(
        None,
        description="Data de início da importação (YYYY-MM-DD). Padrão: hoje − 90 dias.",
    ),
    end_date: Optional[date] = Query(
        None,
        description="Data de fim da importação (YYYY-MM-DD). Padrão: hoje.",
    ),
    current_user: UserResponseDTO = Depends(get_current_user),
    scope: CertifiedLedgerScope = Depends(require_certified_legacy_financial_scope),
):
    """Importa transações do Pierre Finance para o banco de dados local."""
    try:
        result = await PierreImportPipeline(scope).run(start_date, end_date)
        return SyncResultDTO(
            status="success", imported=result["transactions"], skipped=result["skipped"], errors=0,
            accounts_synced=result["accounts"], duration_seconds=result["duration_seconds"],
            date_range_start=result["date_range_start"], date_range_end=result["date_range_end"],
        )
    except LedgerScopeDenied:
        raise
    except ValueError:
        raise HTTPException(status_code=422, detail="Importação recusada: dados incompletos ou inconsistentes") from None
    except Exception:
        raise HTTPException(status_code=502, detail="Importação não concluída; nenhuma gravação financeira foi confirmada") from None


@router.get("/import-status", response_model=dict)
async def get_import_status(
    current_user: UserResponseDTO = Depends(get_current_user),
    scope: CertifiedLedgerScope = Depends(require_certified_legacy_financial_scope),
):
    """Retorna informações básicas sobre o estado atual da importação Pierre."""
    from backend.core.config import settings
    has_key = bool(settings.PIERRE_API_KEY)
    return {
        "pierre_configured": has_key,
        "message": "Pierre API key configurada" if has_key else "PIERRE_API_KEY não definida",
    }



