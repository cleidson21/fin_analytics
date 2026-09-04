"""
governance_router.py — Sprint 2.8: Endpoints de Governança Financeira

Endpoints:
  GET  /api/v1/governance/transactions              — lista com filtros
  GET  /api/v1/governance/transactions/{prov}/{ext} — detalhe completo
  PATCH /api/v1/governance/transactions/{prov}/{ext}/classify — classificar
  GET  /api/v1/governance/transactions/{prov}/{ext}/history   — audit log
  POST /api/v1/governance/transactions/{prov}/{ext}/rollback/{audit_id} — rollback
  GET  /api/v1/governance/summary                  — totais para Controle Financeiro
"""

import json
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator

from backend.database.session import SessionLocal
from backend.domains.pierre.repository import (
    TransactionRepository,
    GovernanceRepository,
    GovernedFinancialQuery,
)
from backend.domains.pierre.models import Transaction, GovernanceAuditLog, Account
from backend.api.dependencies.auth import get_current_user
from backend.application.dtos.user_response_dto import UserResponseDTO

router = APIRouter(prefix="/governance", tags=["Governance"])


# ==========================================================================
# SCHEMAS DE RESPOSTA
# ==========================================================================

class RawDataOut(BaseModel):
    """Dados originais da API — readonly."""
    provider: str
    external_id: str
    account_external_id: str
    account_name: Optional[str] = None       # nome legível da conta (ex: Nubank)
    description: str
    original_description: Optional[str] = None
    category: Optional[str] = None
    original_category: Optional[str] = None
    amount: float
    currency: str
    date: str
    status: str
    type: str
    merchant_name: Optional[str] = None
    bill_id: Optional[str] = None
    installment_number: Optional[int] = None
    total_installments: Optional[int] = None
    receiver_name: Optional[str] = None
    payer_name: Optional[str] = None


class GovernanceDataOut(BaseModel):
    """Estado atual de governança — editável pelo usuário."""
    governance_status: str          # PENDING | CLASSIFIED
    economic_classification: Optional[str] = None  # ENTRADA | SAIDA | IGNORAR | None
    investment_name: Optional[str] = None
    notes: Optional[str] = None
    governed_at: Optional[str] = None


class AuditEventOut(BaseModel):
    """Evento de auditoria no histórico de governança."""
    id: int
    provider: Optional[str] = None
    external_id: Optional[str] = None
    action: str                    # CREATE_CLASSIFICATION | UPDATE_CLASSIFICATION | ROLLBACK
    before_json: Optional[Dict[str, Any]] = None
    after_json: Optional[Dict[str, Any]] = None
    changed_at: str
    changed_by: Optional[str] = None
    reason: Optional[str] = None


class TransactionGovernanceOut(BaseModel):
    """Transação com dados RAW + governança para a tabela de governança."""
    raw: RawDataOut
    governance: GovernanceDataOut


class TransactionDetailOut(BaseModel):
    """Detalhe completo: RAW + governança + histórico de eventos."""
    raw: RawDataOut
    governance: GovernanceDataOut
    history: List[AuditEventOut]


class ClassifyRequest(BaseModel):
    """
    Payload para classificação manual de uma transação.
    Nunca aceita governance_status, provider ou external_id — esses são imutáveis ou controlados internamente.
    """
    economic_classification: str   # ENTRADA | SAIDA | IGNORAR
    investment_name: Optional[str] = None
    notes: Optional[str] = None
    reason: Optional[str] = None

    @field_validator('economic_classification')
    @classmethod
    def validate_classification(cls, v: str) -> str:
        allowed = {'ENTRADA', 'SAIDA', 'IGNORAR'}
        if v not in allowed:
            raise ValueError(f"economic_classification deve ser um de: {allowed}")
        return v


class SummaryOut(BaseModel):
    """Totais financeiros baseados em governança — para Controle Financeiro."""
    total_entrada: float
    total_saida: float
    resultado: float
    pending_count: int
    classified_count: int
    ignored_count: int


# ==========================================================================
# HELPERS
# ==========================================================================

def _tx_to_raw(tx: Transaction, account_name: Optional[str] = None) -> RawDataOut:
    return RawDataOut(
        provider=tx.provider,
        external_id=tx.external_id,
        account_external_id=tx.account_external_id or "",
        account_name=account_name,
        description=tx.description,
        original_description=tx.original_description,
        category=tx.category,
        original_category=tx.original_category,
        amount=float(tx.amount or 0),
        currency=tx.currency or "BRL",
        date=tx.date.isoformat() if tx.date else "",
        status=tx.status or "",
        type=tx.type or "",
        merchant_name=tx.merchant_name,
        bill_id=tx.bill_id,
        installment_number=tx.installment_number,
        total_installments=tx.total_installments,
        receiver_name=tx.receiver_name,
        payer_name=tx.payer_name,
    )


def _tx_to_gov(tx: Transaction) -> GovernanceDataOut:
    return GovernanceDataOut(
        governance_status=tx.governance_status or "PENDING",
        economic_classification=tx.economic_classification,
        investment_name=tx.investment_name,
        notes=tx.notes,
        governed_at=tx.governed_at.isoformat() if tx.governed_at else None,
    )


def _audit_to_out(ev: GovernanceAuditLog) -> AuditEventOut:
    return AuditEventOut(
        id=ev.id,
        provider=ev.provider,
        external_id=ev.external_id,
        action=ev.action,
        before_json=json.loads(ev.before_json) if ev.before_json else None,
        after_json=json.loads(ev.after_json) if ev.after_json else None,
        changed_at=ev.changed_at.isoformat() if ev.changed_at else "",
        changed_by=ev.changed_by,
        reason=ev.reason,
    )


# ==========================================================================
# ENDPOINTS
# ==========================================================================

@router.get("/transactions", response_model=Dict[str, Any])
def list_transactions(
    governance_status: Optional[str] = Query(None, description="PENDING | CLASSIFIED"),
    economic_classification: Optional[str] = Query(None, description="ENTRADA | SAIDA | IGNORAR"),
    account_external_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD — usa transactions.date"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD — usa transactions.date"),
    sort_dir: str = Query("desc", description="asc | desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: UserResponseDTO = Depends(get_current_user),
):
    """
    Lista transações com dados RAW + governança.
    Filtro de período usa transactions.date (data da API), não governed_at.
    """
    tx_repo = TransactionRepository()
    db = SessionLocal()
    try:
        items, total = tx_repo.list_with_governance(
            db,
            governance_status=governance_status,
            economic_classification=economic_classification,
            account_external_id=account_external_id,
            category=category,
            start_date=start_date,
            end_date=end_date,
            sort_dir=sort_dir,
            page=page,
            page_size=page_size,
        )

        # Busca nomes das contas em batch para evitar N+1 queries
        account_ids = list({(tx.account_provider, tx.account_external_id) for tx in items})
        account_names: dict = {}
        for acc_provider, acc_ext_id in account_ids:
            acc = db.query(Account).filter(
                Account.provider == acc_provider,
                Account.external_id == acc_ext_id,
            ).first()
            if acc:
                account_names[(acc_provider, acc_ext_id)] = acc.name

        result = [
            TransactionGovernanceOut(
                raw=_tx_to_raw(tx, account_names.get((tx.account_provider, tx.account_external_id))),
                governance=_tx_to_gov(tx)
            )
            for tx in items
        ]
        db.expunge_all()
    finally:
        db.close()

    return {
        "items": [r.model_dump() for r in result],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/transactions/{provider}/{external_id}", response_model=TransactionDetailOut)
def get_transaction_detail(
    provider: str,
    external_id: str,
    current_user: UserResponseDTO = Depends(get_current_user),
):
    """
    Detalhe completo de uma transação: dados RAW + governança + histórico de eventos de auditoria.
    """
    tx_repo = TransactionRepository()
    gov_repo = GovernanceRepository()

    db = SessionLocal()
    try:
        tx = tx_repo.get_by_external_id(db, provider, external_id)
        if not tx:
            raise HTTPException(status_code=404, detail="Transação não encontrada")

        history = gov_repo.get_audit_log(db, provider, external_id)
        raw = _tx_to_raw(tx)
        gov = _tx_to_gov(tx)
        hist_out = [_audit_to_out(ev) for ev in history]
        db.expunge_all()
    finally:
        db.close()

    return TransactionDetailOut(raw=raw, governance=gov, history=hist_out)


@router.patch("/transactions/{provider}/{external_id}/classify", response_model=TransactionGovernanceOut)
def classify_transaction(
    provider: str,
    external_id: str,
    payload: ClassifyRequest,
    current_user: UserResponseDTO = Depends(get_current_user),
):
    """
    Classifica manualmente uma transação.

    ATÔMICO: altera governança e insere audit_log em uma única transação de banco.
    Se qualquer operação falhar, nenhuma é aplicada.

    Valores válidos: economic_classification = ENTRADA | SAIDA | IGNORAR
    """
    tx_repo = TransactionRepository()

    db = SessionLocal()
    try:
        tx = tx_repo.classify(
            db,
            provider=provider,
            external_id=external_id,
            economic_classification=payload.economic_classification,
            investment_name=payload.investment_name,
            notes=payload.notes,
            reason=payload.reason,
        )
        db.commit()
        result = TransactionGovernanceOut(raw=_tx_to_raw(tx), governance=_tx_to_gov(tx))
        db.expunge_all()
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao classificar: {e}")
    finally:
        db.close()

    return result


@router.get("/transactions/{provider}/{external_id}/history", response_model=List[AuditEventOut])
def get_history(
    provider: str,
    external_id: str,
    current_user: UserResponseDTO = Depends(get_current_user),
):
    """
    Histórico completo de eventos de governança para uma transação.
    Cada evento contém: action, before_json, after_json, changed_at, reason.

    A UI deve apresentar cada evento como: 'Restaurar estado ANTES desta mudança'.
    Não usar numeração de versão — pode ser confusa quando ROLLBACKs são intercalados.
    """
    gov_repo = GovernanceRepository()
    db = SessionLocal()
    try:
        events = gov_repo.get_audit_log(db, provider, external_id)
        result = [_audit_to_out(ev) for ev in events]
        db.expunge_all()
    finally:
        db.close()
    return result


@router.post("/transactions/{provider}/{external_id}/rollback/{audit_id}", response_model=TransactionGovernanceOut)
def rollback_to_event(
    provider: str,
    external_id: str,
    audit_id: int,
    reason: Optional[str] = Query(None),
    current_user: UserResponseDTO = Depends(get_current_user),
):
    """
    Restaura o estado de governança para o snapshot 'before_json' do evento especificado.
    ATÔMICO: restaura governança + insere audit_log action=ROLLBACK em uma única transação.
    """
    gov_repo = GovernanceRepository()

    db = SessionLocal()
    try:
        tx = gov_repo.rollback_to_event(
            db,
            provider=provider,
            external_id=external_id,
            audit_id=audit_id,
            reason=reason,
        )
        db.commit()
        result = TransactionGovernanceOut(raw=_tx_to_raw(tx), governance=_tx_to_gov(tx))
        db.expunge_all()
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro no rollback: {e}")
    finally:
        db.close()

    return result


@router.get("/summary", response_model=SummaryOut)
def get_financial_summary(
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD — usa transactions.date"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD — usa transactions.date"),
    economic_classification: Optional[str] = Query(None, description="ENTRADA | SAIDA | IGNORAR — filtra os totais"),
    category: Optional[str] = Query(None, description="Nome da categoria RAW"),
    current_user: UserResponseDTO = Depends(get_current_user),
):
    """
    Totais financeiros baseados em classificações governadas.

    Suporta os mesmos filtros da listagem para que os KPIs reflitam
    exatamente o subconjunto de transações visíveis na tela.

    pending_count sempre reflete o período completo (sem filtro de tipo/categoria).
    """
    query = GovernedFinancialQuery()
    db = SessionLocal()
    try:
        summary = query.get_summary(
            db,
            start_date=start_date,
            end_date=end_date,
            economic_classification=economic_classification,
            category=category,
        )
        db.expunge_all()
    finally:
        db.close()
    return SummaryOut(**summary)


@router.get("/audit-log", response_model=List[AuditEventOut])
def get_global_audit_log(
    limit: int = Query(100, ge=1, le=500, description="Máximo de eventos a retornar"),
    action: Optional[str] = Query(None, description="Filtrar por ação: CREATE_CLASSIFICATION, UPDATE_CLASSIFICATION, ROLLBACK"),
    provider: Optional[str] = Query(None, description="Filtrar por provedor"),
    current_user: UserResponseDTO = Depends(get_current_user),
):
    """
    Histórico global de eventos de governança (governance_audit_log).

    Retorna os eventos mais recentes de todas as transações, ordenados por data decrescente.
    Use action= para filtrar por tipo de evento.
    Use provider= para filtrar por provedor (ex: pierre).

    IMPORTANTE: Este endpoint expõe o audit_log de GOVERNANÇA (classificações, rollbacks).
    Não confundir com logs de importação — esses são um conceito separado.
    """
    db = SessionLocal()
    try:
        q = db.query(GovernanceAuditLog)
        if action:
            q = q.filter(GovernanceAuditLog.action == action.upper())
        if provider:
            q = q.filter(GovernanceAuditLog.provider == provider)
        events = q.order_by(GovernanceAuditLog.changed_at.desc()).limit(limit).all()
        result = [_audit_to_out(ev) for ev in events]
        db.expunge_all()
    finally:
        db.close()
    return result
