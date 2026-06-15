from fastapi import APIRouter, Depends, Query
from app.api.services.governance_service import GovernanceService
from app.api.deps import require_admin

router = APIRouter(prefix="/governance/learning", tags=["Learning & Memory"], dependencies=[Depends(require_admin)])

def get_db():
    return GovernanceService()

@router.get("/metrics")
def get_learning_metrics(db: GovernanceService = Depends(get_db)):
    """Retorna os KPIs gerais da Memória Financeira."""
    return db.get_learning_metrics()

@router.get("/rules/top")
def get_top_rules(
    limit: int = Query(20, description="Limite de regras"),
    db: GovernanceService = Depends(get_db)
):
    """Retorna o ranking das regras mais utilizadas."""
    return db.get_top_rules(limit=limit)

@router.get("/rules/problematic")
def get_problematic_rules(
    limit: int = Query(20, description="Limite de regras"),
    db: GovernanceService = Depends(get_db)
):
    """Retorna regras degradadas (miss_count > 0)."""
    return db.get_problematic_rules(limit=limit)

@router.get("/rules")
def get_rules_audit(
    limit: int = Query(100, description="Limite de paginação"),
    offset: int = Query(0, description="Offset de paginação"),
    status: str = Query(None, description="Filtro por status: OBSERVING, ACTIVE, QUARANTINED, RETIRED"),
    db: GovernanceService = Depends(get_db)
):
    """Retorna o histórico e estado atual de todas as regras da Memória Financeira."""
    return db.get_rules_audit(limit=limit, offset=offset, status=status)
