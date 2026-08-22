"""
repository.py — Sprint 2.8: Camada de Governança Financeira Manual

Separação explícita entre camadas:
  IDENTITY_FIELDS   — imutáveis por qualquer operação
  ALLOWED_RAW_FIELDS — atualizáveis pelo upsert de sync
  GOVERNANCE_FIELDS  — jamais tocados pela API

Regras:
  1. upsert(): INSERT para nova transação (PENDING) | UPDATE RAW para existente (preserva governança)
  2. classify(): atômico — UPDATE governança + INSERT audit_log em uma única transação de banco
  3. rollback_to_event(): atômico — restaura before_json + INSERT audit ROLLBACK
  4. GovernedFinancialQuery: centralizador único de cálculos financeiros (sem WHERE espalhado)
"""

import json
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert

from backend.domains.pierre.models import (
    Account,
    Transaction,
    Category,
    SyncState,
    SyncHistory,
    GovernanceAuditLog,
)

# ==========================================================================
# SEPARAÇÃO EXPLÍCITA DE CAMPOS — não é convenção implícita
# ==========================================================================

# Identidade da transação — jamais alterada por nenhuma operação
IDENTITY_FIELDS = frozenset({
    'provider',      # quem originou a transação (ex: 'pierre')
    'external_id',   # ID único emitido pela API
})

# Dados da API — atualizáveis pelo upsert de sync
# account_provider/account_external_id são atributos de conta, não identidade da transação.
# A API pode corrigi-los legitimamente (ex: reatribuição de conta no Open Finance).
ALLOWED_RAW_FIELDS = frozenset({
    'account_provider', 'account_external_id',
    'description', 'original_description',
    'category', 'original_category',
    'amount', 'currency', 'date', 'status', 'type',
    'merchant_name', 'bill_id',
    'installment_number', 'total_installments',
    'purchase_date', 'receiver_name', 'payer_name',
    'manual_transaction', 'extra_json',
})

# Governança — propriedade do usuário; jamais aparecem no payload da API
GOVERNANCE_FIELDS = frozenset({
    'governance_status',
    'economic_classification',
    'investment_name',
    'notes',
    'governed_at',
})


def _governance_snapshot(tx: Transaction) -> dict:
    """Captura o estado atual de governança de uma transação como dict."""
    return {
        'governance_status': tx.governance_status,
        'economic_classification': tx.economic_classification,
        'investment_name': tx.investment_name,
        'notes': tx.notes,
        'governed_at': tx.governed_at.isoformat() if tx.governed_at else None,
    }


# ==========================================================================
# ACCOUNT REPOSITORY
# ==========================================================================

class AccountRepository:
    def upsert(self, db: Session, account_data: dict) -> Account:
        stmt = insert(Account).values(**account_data)
        update_dict = {c.name: c for c in stmt.excluded if c.name not in ['provider', 'external_id']}
        if update_dict:
            stmt = stmt.on_conflict_do_update(
                index_elements=['provider', 'external_id'],
                set_=update_dict
            )
        else:
            stmt = stmt.on_conflict_do_nothing(index_elements=['provider', 'external_id'])
        db.execute(stmt)
        return self.get_by_external_id(db, account_data['provider'], account_data['external_id'])

    def get_by_external_id(self, db: Session, provider: str, external_id: str) -> Optional[Account]:
        return db.query(Account).filter(
            Account.provider == provider,
            Account.external_id == external_id
        ).first()

    def list_all(self, db: Session) -> List[Account]:
        return db.query(Account).all()


# ==========================================================================
# TRANSACTION REPOSITORY
# ==========================================================================

class TransactionRepository:
    """
    Regra fundamental do upsert:

    Nova transação (external_id não existe):
      → INSERT com todos os campos RAW + governance_status='PENDING'

    Transação existente (external_id já existe):
      → UPDATE apenas ALLOWED_RAW_FIELDS
      → PRESERVA governance_status, economic_classification e todos os campos de governança
    """

    def upsert(self, db: Session, transaction_data: dict) -> Transaction:
        provider = transaction_data['provider']
        external_id = transaction_data['external_id']

        existing = self.get_by_external_id(db, provider, external_id)

        if existing:
            # Transação existente: atualizar somente campos RAW permitidos
            # Governança é intocável neste caminho
            raw_update = {
                k: v for k, v in transaction_data.items()
                if k in ALLOWED_RAW_FIELDS
            }
            for field, value in raw_update.items():
                setattr(existing, field, value)
            # Nota: não tocar em governance_status, economic_classification, etc.
            return existing
        else:
            # Nova transação: inserir com todos os campos + governance PENDING
            safe_data = {
                k: v for k, v in transaction_data.items()
                if k not in GOVERNANCE_FIELDS  # governança não vem da API
            }
            tx = Transaction(**safe_data)
            tx.governance_status = 'PENDING'
            tx.economic_classification = None
            tx.investment_name = None
            tx.notes = None
            tx.governed_at = None
            db.add(tx)
            return tx

    def get_by_external_id(self, db: Session, provider: str, external_id: str) -> Optional[Transaction]:
        return db.query(Transaction).filter(
            Transaction.provider == provider,
            Transaction.external_id == external_id
        ).first()

    def list_all(self, db: Session) -> List[Transaction]:
        return db.query(Transaction).all()

    def classify(
        self,
        db: Session,
        provider: str,
        external_id: str,
        economic_classification: str,
        investment_name: Optional[str] = None,
        notes: Optional[str] = None,
        reason: Optional[str] = None,
        changed_by: Optional[str] = None,
    ) -> Transaction:
        """
        Altera a classificação econômica de uma transação.

        ATÔMICO: UPDATE de governança + INSERT de audit_log em uma única transação de banco.
        Se qualquer operação falhar, nenhuma é aplicada.

        Valores válidos para economic_classification: ENTRADA | SAIDA | IGNORAR
        """
        tx = self.get_by_external_id(db, provider, external_id)
        if not tx:
            raise ValueError(f"Transação não encontrada: {provider}/{external_id}")

        # Capturar estado anterior para o audit log
        before = _governance_snapshot(tx)

        # Determinar tipo de ação
        if tx.governance_status == 'PENDING':
            action = 'CREATE_CLASSIFICATION'
        else:
            action = 'UPDATE_CLASSIFICATION'

        # Aplicar nova governança
        tx.governance_status = 'CLASSIFIED'
        tx.economic_classification = economic_classification
        tx.investment_name = investment_name
        tx.notes = notes
        tx.governed_at = datetime.utcnow()

        # Capturar estado posterior
        after = _governance_snapshot(tx)

        # Inserir registro de auditoria (INSERT-only, imutável)
        audit = GovernanceAuditLog(
            provider=provider,
            external_id=external_id,
            action=action,
            before_json=json.dumps(before, ensure_ascii=False),
            after_json=json.dumps(after, ensure_ascii=False),
            changed_at=datetime.utcnow(),
            changed_by=changed_by,
            reason=reason,
        )
        db.add(audit)

        # Ambos (UPDATE tx + INSERT audit) serão commitados ou revertidos juntos
        # pelo contexto de transação do chamador (with db.begin() no router)
        return tx

    def list_with_governance(
        self,
        db: Session,
        governance_status: Optional[str] = None,
        economic_classification: Optional[str] = None,
        account_external_id: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sort_dir: str = "desc",
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[List[Transaction], int]:
        """Lista transações com filtros de governança. Usa transactions.date para período."""
        q = db.query(Transaction)

        if governance_status:
            q = q.filter(Transaction.governance_status == governance_status)
        if economic_classification:
            q = q.filter(Transaction.economic_classification == economic_classification)
        if account_external_id:
            q = q.filter(Transaction.account_external_id == account_external_id)
        if category:
            q = q.filter(Transaction.category == category)
        if start_date:
            s_date = f"{start_date} 00:00:00" if len(start_date) == 10 else start_date
            q = q.filter(Transaction.date >= s_date)
        if end_date:
            e_date = f"{end_date} 23:59:59" if len(end_date) == 10 else end_date
            q = q.filter(Transaction.date <= e_date)

        total = q.count()
        if sort_dir.lower() == "asc":
            items = q.order_by(Transaction.date.asc()).offset((page - 1) * page_size).limit(page_size).all()
        else:
            items = q.order_by(Transaction.date.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return items, total


# ==========================================================================
# GOVERNANCE REPOSITORY
# ==========================================================================

class GovernanceRepository:
    """
    Gerencia o audit log e operações de rollback de governança.

    Todas as operações que alteram governança são atômicas:
    UPDATE transactions + INSERT governance_audit_log em uma transação de banco.
    """

    def get_audit_log(
        self,
        db: Session,
        provider: str,
        external_id: str,
    ) -> List[GovernanceAuditLog]:
        """Retorna histórico de eventos de governança ordenado do mais recente ao mais antigo."""
        return (
            db.query(GovernanceAuditLog)
            .filter(
                GovernanceAuditLog.provider == provider,
                GovernanceAuditLog.external_id == external_id,
            )
            .order_by(GovernanceAuditLog.changed_at.desc())
            .all()
        )

    def rollback_to_event(
        self,
        db: Session,
        provider: str,
        external_id: str,
        audit_id: int,
        reason: Optional[str] = None,
        changed_by: Optional[str] = None,
    ) -> Transaction:
        """
        Restaura o estado de governança para o snapshot 'before_json' do evento especificado.

        Semântica: "voltar para o estado que existia ANTES desta mudança ocorrer."

        ATÔMICO: restaura governança + insere audit_log action=ROLLBACK em uma transação.
        O rollback em si também fica registrado no audit log para rastreabilidade completa.
        """
        # Buscar o evento de auditoria referenciado
        audit_event = db.query(GovernanceAuditLog).filter(
            GovernanceAuditLog.id == audit_id,
            GovernanceAuditLog.provider == provider,
            GovernanceAuditLog.external_id == external_id,
        ).first()

        if not audit_event:
            raise ValueError(f"Evento de auditoria {audit_id} não encontrado para {provider}/{external_id}")

        # Buscar transação atual
        tx_repo = TransactionRepository()
        tx = tx_repo.get_by_external_id(db, provider, external_id)
        if not tx:
            raise ValueError(f"Transação não encontrada: {provider}/{external_id}")

        # Capturar estado atual (será o 'before' do evento de rollback)
        current_state = _governance_snapshot(tx)

        # Determinar estado a restaurar (before_json do evento referenciado)
        if audit_event.before_json:
            restore_state = json.loads(audit_event.before_json)
        else:
            # O evento referenciado era a primeira classificação; restaurar PENDING
            restore_state = {
                'governance_status': 'PENDING',
                'economic_classification': None,
                'investment_name': None,
                'notes': None,
                'governed_at': None,
            }

        # Aplicar estado restaurado na transação
        tx.governance_status = restore_state.get('governance_status', 'PENDING')
        tx.economic_classification = restore_state.get('economic_classification')
        tx.investment_name = restore_state.get('investment_name')
        tx.notes = restore_state.get('notes')
        tx.governed_at = datetime.utcnow()  # timestamp do rollback, não do estado original

        # Registrar o rollback no audit log (INSERT-only — rastreabilidade completa)
        rollback_audit = GovernanceAuditLog(
            provider=provider,
            external_id=external_id,
            action='ROLLBACK',
            before_json=json.dumps(current_state, ensure_ascii=False),
            after_json=json.dumps(restore_state, ensure_ascii=False),
            changed_at=datetime.utcnow(),
            changed_by=changed_by,
            reason=reason or f"Rollback do evento #{audit_id}",
        )
        db.add(rollback_audit)

        return tx


# ==========================================================================
# GOVERNED FINANCIAL QUERY — camada única de leitura financeira
# ==========================================================================

class GovernedFinancialQuery:
    """
    Centralizador único para cálculos financeiros baseados em governança.

    Regras:
      - Somente transações com governance_status = 'CLASSIFIED' entram nos totais.
      - PENDING não contabiliza (mas é incluído no pending_count).
      - IGNORAR é uma decisão válida — excluída dos totais, não do histórico.
      - Período filtrado por transactions.date (data da API), não governed_at.
      - amount mantém o valor RAW original; a classificação determina o sinal econômico.
    """

    def get_summary(
        self,
        db: Session,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        economic_classification: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retorna totais financeiros e contagem de pendências.

        Filtros suportados:
          - start_date / end_date  : período (transactions.date)
          - economic_classification: ENTRADA | SAIDA | IGNORAR
          - category               : nome da categoria RAW

        pending_count é sempre calculado sem filtro de tipo/categoria
        para que o aviso de pendências reflita o período completo.
        """
        base_q = db.query(Transaction)
        if start_date:
            s_date = f"{start_date} 00:00:00" if len(start_date) == 10 else start_date
            base_q = base_q.filter(Transaction.date >= s_date)
        if end_date:
            e_date = f"{end_date} 23:59:59" if len(end_date) == 10 else end_date
            base_q = base_q.filter(Transaction.date <= e_date)

        # pending_count: sem filtro de tipo para o aviso global do período
        pending_count = base_q.filter(Transaction.governance_status == 'PENDING').count()

        # Totais: aplica filtros adicionais
        classified_q = base_q.filter(Transaction.governance_status == 'CLASSIFIED')
        if economic_classification:
            classified_q = classified_q.filter(
                Transaction.economic_classification == economic_classification
            )
        if category:
            classified_q = classified_q.filter(Transaction.category == category)

        classified_tx = classified_q.all()

        total_entrada = Decimal('0')
        total_saida = Decimal('0')
        classified_count = 0
        ignored_count = 0

        for tx in classified_tx:
            classified_count += 1
            amt = abs(tx.amount or Decimal('0'))
            if tx.economic_classification == 'ENTRADA':
                total_entrada += amt
            elif tx.economic_classification == 'SAIDA':
                total_saida += amt
            elif tx.economic_classification == 'IGNORAR':
                ignored_count += 1

        resultado = total_entrada - total_saida

        return {
            'total_entrada': float(total_entrada),
            'total_saida': float(total_saida),
            'resultado': float(resultado),
            'pending_count': pending_count,
            'classified_count': classified_count,
            'ignored_count': ignored_count,
        }

    def get_monthly_kpis(self, db: Session, month: str) -> Dict[str, Any]:
        """
        Retorna KPIs mensais para o Dashboard — usa governança do Pierre.

        Calcula m\u00eas atual e anterior para mostrar varia\u00e7\u00e3o percentual.
        S\u00f3 considera transa\u00e7\u00f5es CLASSIFIED.
        """
        def _totals_for_month(ym: str) -> Dict[str, float]:
            year, mo = int(ym[:4]), int(ym[5:7])
            import calendar
            last_day = calendar.monthrange(year, mo)[1]
            start = f"{ym}-01"
            end = f"{ym}-{last_day:02d}"
            txs = (
                db.query(Transaction)
                .filter(
                    Transaction.governance_status == 'CLASSIFIED',
                    Transaction.date >= start,
                    Transaction.date <= end,
                )
                .all()
            )
            entrada = sum(float(abs(t.amount or 0)) for t in txs if t.economic_classification == 'ENTRADA')
            saida = sum(float(abs(t.amount or 0)) for t in txs if t.economic_classification == 'SAIDA')
            return {'entrada': entrada, 'saida': saida, 'saldo': entrada - saida}

        # M\u00eas atual e m\u00eas anterior
        y, m = int(month[:4]), int(month[5:7])
        prev_total = (y * 12 + m - 1) - 1
        prev_month = f"{prev_total // 12}-{(prev_total % 12) + 1:02d}"

        current = _totals_for_month(month)
        previous = _totals_for_month(prev_month)

        def _kpi(cur: float, prev: float) -> Dict[str, float]:
            if prev == 0:
                delta = 100.0 if cur > 0 else 0.0
            else:
                delta = round(((cur - prev) / abs(prev)) * 100, 1)
            return {'current': cur, 'previous': prev, 'delta_pct': delta}

        return {
            'month': month,
            'receitas': _kpi(current['entrada'], previous['entrada']),
            'despesas': _kpi(current['saida'], previous['saida']),
            'saldo_liquido': _kpi(current['saldo'], previous['saldo']),
            'patrimonio': _kpi(current['saldo'], previous['saldo']),
        }

    def get_pacing_data(self, db: Session, month: str) -> Dict[str, Any]:
        """
        Ritmo de Gastos — dados di\u00e1rios para o gr\u00e1fico de linha.

        Retorna gastos (SAIDA) acumulados dia a dia no m\u00eas atual vs m\u00eas anterior.
        """
        import calendar
        from collections import defaultdict

        y, m_int = int(month[:4]), int(month[5:7])
        last_day = calendar.monthrange(y, m_int)[1]
        start = f"{month}-01"
        end = f"{month}-{last_day:02d}"

        # M\u00eas anterior
        prev_total = (y * 12 + m_int - 1) - 1
        prev_month = f"{prev_total // 12}-{(prev_total % 12) + 1:02d}"
        p_y, p_m = int(prev_month[:4]), int(prev_month[5:7])
        p_last = calendar.monthrange(p_y, p_m)[1]
        prev_start = f"{prev_month}-01"
        prev_end = f"{prev_month}-{p_last:02d}"

        def _daily_totals(start_dt: str, end_dt: str) -> Dict[int, float]:
            txs = (
                db.query(Transaction)
                .filter(
                    Transaction.governance_status == 'CLASSIFIED',
                    Transaction.economic_classification == 'SAIDA',
                    Transaction.date >= start_dt,
                    Transaction.date <= end_dt,
                )
                .all()
            )
            by_day: Dict[int, float] = defaultdict(float)
            for tx in txs:
                day = tx.date.day if tx.date else 0
                by_day[day] += float(abs(tx.amount or 0))
            return by_day

        current_by_day = _daily_totals(start, end)
        prev_by_day = _daily_totals(prev_start, prev_end)

        daily_data = []
        for day in range(1, last_day + 1):
            daily_data.append({
                'date': f"{month}-{day:02d}",
                'current_amount': current_by_day.get(day, 0),
                'previous_amount': prev_by_day.get(day, 0),
            })

        current_total = sum(current_by_day.values())
        prev_total_amt = sum(prev_by_day.values())
        if prev_total_amt == 0:
            delta = 100.0 if current_total > 0 else 0.0
        else:
            delta = round(((current_total - prev_total_amt) / abs(prev_total_amt)) * 100, 1)

        trend = 'up' if delta > 0 else 'down' if delta < 0 else 'stable'
        severity = 'high' if delta > 20 else 'medium' if delta > 5 else 'low'

        return {
            'current_month': month,
            'previous_month': prev_month,
            'current_expenses': current_total,
            'previous_expenses': prev_total_amt,
            'delta_percentage': delta,
            'trend': trend,
            'severity': severity,
            'message': f"Gastos {'acima' if delta > 0 else 'abaixo'} do m\u00eas anterior",
            'daily_data': daily_data,
        }

    def get_heatmap_data(self, db: Session, month: str) -> List[Dict[str, Any]]:
        """
        Mapa de Calor — intensidade de gastos por dia.

        Retorna todos os dias do m\u00eas com o valor total (SAIDA CLASSIFIED)
        e intensidade normalizada 0\u20131 baseada no maior dia do m\u00eas.
        """
        import calendar
        from collections import defaultdict

        y, m_int = int(month[:4]), int(month[5:7])
        last_day = calendar.monthrange(y, m_int)[1]
        start = f"{month}-01 00:00:00"
        end = f"{month}-{last_day:02d} 23:59:59"

        txs = (
            db.query(Transaction)
            .filter(
                Transaction.governance_status == 'CLASSIFIED',
                Transaction.economic_classification == 'SAIDA',
                Transaction.date >= start,
                Transaction.date <= end,
            )
            .all()
        )

        by_day: Dict[int, float] = defaultdict(float)
        for tx in txs:
            day = tx.date.day if tx.date else 0
            by_day[day] += float(abs(tx.amount or 0))

        max_amount = max(by_day.values()) if by_day else 1

        result = []
        for day in range(1, last_day + 1):
            amt = by_day.get(day, 0)
            result.append({
                'date': f"{month}-{day:02d}",
                'amount': str(round(amt, 2)),
                'intensity': round(amt / max_amount, 4) if max_amount > 0 else 0,
            })

        return result

    def get_categories_breakdown(self, db: Session, month: str) -> List[Dict[str, Any]]:
        """
        Resumo de gastos por categoria para o Top Categories e tela de Categorias.
        
        Soma (em valor absoluto) as transações do mês:
          governance_status = 'CLASSIFIED'
          economic_classification = 'SAIDA'
        Agrupa por category e ordena do maior para o menor gasto.
        """
        import calendar
        from sqlalchemy import func

        y, m_int = int(month[:4]), int(month[5:7])
        last_day = calendar.monthrange(y, m_int)[1]
        start = f"{month}-01 00:00:00"
        end = f"{month}-{last_day:02d} 23:59:59"

        results = (
            db.query(
                Transaction.category,
                func.sum(func.abs(Transaction.amount)).label('total')
            )
            .filter(
                Transaction.governance_status == 'CLASSIFIED',
                Transaction.economic_classification == 'SAIDA',
                Transaction.date >= start,
                Transaction.date <= end,
            )
            .group_by(Transaction.category)
            .order_by(func.sum(func.abs(Transaction.amount)).desc())
            .all()
        )
        
        breakdown = []
        for cat, total in results:
            breakdown.append({
                "category": cat or "Uncategorized",
                "total": float(total or 0)
            })
            
        return breakdown

# ==========================================================================
# CATEGORY REPOSITORY
# ==========================================================================

class CategoryRepository:
    def insert_if_not_exists(self, db: Session, category_data: dict) -> Category:
        stmt = insert(Category).values(**category_data)
        stmt = stmt.on_conflict_do_nothing(index_elements=['provider', 'name'])
        db.execute(stmt)
        return db.query(Category).filter(
            Category.provider == category_data['provider'],
            Category.name == category_data['name']
        ).first()

    def list_all(self, db: Session) -> List[Category]:
        return db.query(Category).all()


# ==========================================================================
# SYNC REPOSITORY
# ==========================================================================

class SyncRepository:
    def update_state(self, db: Session, state_data: dict) -> SyncState:
        stmt = insert(SyncState).values(**state_data)
        update_dict = {c.name: c for c in stmt.excluded if c.name != 'provider'}
        if update_dict:
            stmt = stmt.on_conflict_do_update(index_elements=['provider'], set_=update_dict)
        else:
            stmt = stmt.on_conflict_do_nothing(index_elements=['provider'])
        db.execute(stmt)
        return self.get_state(db, state_data['provider'])

    def get_state(self, db: Session, provider: str) -> Optional[SyncState]:
        return db.query(SyncState).filter(SyncState.provider == provider).first()

    def create_history(self, db: Session, history_data: dict) -> SyncHistory:
        history = SyncHistory(**history_data)
        db.add(history)
        db.flush()
        return history

    def list_history(self, db: Session, provider: str) -> List[SyncHistory]:
        return db.query(SyncHistory).filter(SyncHistory.provider == provider).all()
