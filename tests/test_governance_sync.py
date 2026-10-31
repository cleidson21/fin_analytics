"""
Teste de Integração — Critério #4 Sprint 2.8

Verifica que uma nova sincronização Pierre NÃO altera governance_status ou
economic_classification de uma transação já classificada.

Confirma também que campos RAW (description, category) CAN ser atualizados.

Execução:
    cd c:\\Users\\Cleidson\\Pictures\\fin_analytics_v2
    python -m pytest tests/test_governance_sync.py -v
"""

import pytest
from datetime import datetime
from decimal import Decimal

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

from backend.domains.pierre.repository import TransactionRepository, GovernanceRepository
from backend.domains.pierre.models import Account, LegacyBase, Transaction


@pytest.fixture
def sessions(tmp_path):
    """Each test starts with one synthetic Pierre transaction and no history."""
    engine = create_engine(f"sqlite:///{(tmp_path / 'governance.db').as_posix()}")

    @event.listens_for(engine, "connect")
    def _foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    LegacyBase.metadata.create_all(engine)
    with engine.connect() as connection:
        actual = connection.execute(text("PRAGMA database_list")).fetchone()[2]
        assert actual == str((tmp_path / "governance.db").resolve())
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory.begin() as db:
        db.add(Account(provider="pierre", external_id="synthetic-account", name="Synthetic", type="BANK"))
        db.add(Transaction(
            provider="pierre", external_id="synthetic-transaction",
            account_provider="pierre", account_external_id="synthetic-account",
            description="Synthetic RAW", amount=Decimal("-42.00"), currency="BRL",
            date=datetime(2026, 7, 5), status="POSTED", type="DEBIT",
        ))
    try:
        yield factory
    finally:
        engine.dispose()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_first_transaction(sessions):
    """Return the synthetic transaction created by the per-test fixture."""
    db = sessions()
    try:
        txs = db.query(Transaction).all()
        assert len(txs) == 1
        tx = txs[0]
        return tx.provider, tx.external_id
    finally:
        db.close()


def get_transaction(sessions, provider: str, external_id: str):
    """Retorna o objeto Transaction do banco."""
    db = sessions()
    try:
        repo = TransactionRepository()
        return repo.get_by_external_id(db, provider, external_id)
    finally:
        db.close()


def classify_transaction(sessions, provider: str, external_id: str, classification: str, reason: str):
    """Classifica a transação e retorna o objeto atualizado."""
    db = sessions()
    try:
        repo = TransactionRepository()
        tx = repo.classify(
            db,
            provider=provider,
            external_id=external_id,
            economic_classification=classification,
            reason=reason,
        )
        db.commit()
        external_id_val = tx.external_id
        return external_id_val
    finally:
        db.close()


def upsert_raw_update(sessions, provider: str, external_id: str, new_description: str, new_category: str):
    """
    Simula o que o sync faz: tenta atualizar campos RAW.
    Usa upsert() do TransactionRepository (mesmo método usado pelo pipeline).
    """
    db = sessions()
    try:
        repo = TransactionRepository()
        tx_data = {
            "provider": provider,
            "external_id": external_id,
            "description": new_description,
            "original_description": new_description,
            "category": new_category,
            "original_category": new_category,
            # campos RAW adicionais que podem mudar via API
            "amount": Decimal("-42.00"),
            "currency": "BRL",
            "date": datetime(2026, 7, 5, 19, 19, 49),  # deve ser objeto datetime
            "status": "POSTED",
            "type": "DEBIT",
        }
        repo.upsert(db, tx_data)  # método correto: TransactionRepository.upsert()
        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------

class TestGovernanceSyncPreservation:
    """
    Critério #4: sync preserva campos de governança.
    """

    def test_classify_then_raw_update_preserves_governance(self, sessions):
        """
        Fluxo completo:
        1. Obter transação existente
        2. Classificar como IGNORAR
        3. Simular sync (atualizar campos RAW via upsert)
        4. Verificar que governance_status e economic_classification foram preservados
        5. Verificar que description/category foram atualizados (RAW pode mudar)
        """
        provider, external_id = get_first_transaction(sessions)

        # PASSO 1: Classificar
        classify_transaction(
            sessions, provider, external_id,
            classification="IGNORAR",
            reason="Teste #4 — classificar antes do sync"
        )

        # Verificar estado ANTES do sync
        tx_before = get_transaction(sessions, provider, external_id)
        assert tx_before is not None, "Transação não encontrada após classificar"
        assert tx_before.governance_status == "CLASSIFIED", (
            f"Esperado CLASSIFIED, obtido: {tx_before.governance_status}"
        )
        assert tx_before.economic_classification == "IGNORAR", (
            f"Esperado IGNORAR, obtido: {tx_before.economic_classification}"
        )

        # PASSO 2: Simular sync (atualizar campos RAW)
        new_description = "Descrição ATUALIZADA pelo sync"
        new_category = "Categoria ATUALIZADA pelo sync"
        upsert_raw_update(sessions, provider, external_id, new_description, new_category)

        # PASSO 3: Verificar APÓS o sync
        tx_after = get_transaction(sessions, provider, external_id)
        assert tx_after is not None

        # Governança DEVE estar preservada
        assert tx_after.governance_status == "CLASSIFIED", (
            f"FALHA #4: governance_status foi alterado para {tx_after.governance_status}. "
            "O sync não pode alterar campos de governança!"
        )
        assert tx_after.economic_classification == "IGNORAR", (
            f"FALHA #4: economic_classification foi alterado para {tx_after.economic_classification}. "
            "O sync não pode alterar campos de governança!"
        )

        # RAW PODE ter mudado (campo description é ALLOWED_RAW_FIELD)
        assert tx_after.description == new_description, (
            f"FALHA: description deveria ser '{new_description}', obtido '{tx_after.description}'. "
            "RAW fields devem ser atualizáveis pelo sync."
        )
        assert tx_after.category == new_category, (
            f"FALHA: category deveria ser '{new_category}', obtido '{tx_after.category}'. "
            "RAW fields devem ser atualizáveis pelo sync."
        )

        print("\nCRITERIO #4 - PASS:")
        print(f"   provider:              {tx_after.provider}")
        print(f"   external_id:           {tx_after.external_id}")
        print(f"   governance_status:     {tx_after.governance_status}  <- preservado")
        print(f"   economic_classification: {tx_after.economic_classification}  <- preservado")
        print(f"   description:           {tx_after.description}  <- atualizado pelo sync")
        print(f"   category:              {tx_after.category}  <- atualizado pelo sync")

    def test_identity_fields_not_changed(self, sessions):
        """
        IDENTITY_FIELDS (provider, external_id) nunca podem mudar.
        """
        provider, external_id = get_first_transaction(sessions)

        # Tentar atualizar com campos extras via upsert (provider/external_id são identity)
        db = sessions()
        try:
            repo = TransactionRepository()
            tx_data = {
                "provider": provider,        # identity — deve ser ignorado no UPDATE
                "external_id": external_id,  # identity — deve ser ignorado no UPDATE
                "description": "Teste identity",
                "amount": -1.0,
                "currency": "BRL",
                "date": datetime(2026, 7, 1, 0, 0, 0),
                "status": "POSTED",
                "type": "DEBIT",
            }
            repo.upsert(db, tx_data)  # método correto
            db.commit()
        finally:
            db.close()

        tx = get_transaction(sessions, provider, external_id)
        assert tx is not None
        assert tx.provider == provider, "provider foi alterado!"
        assert tx.external_id == external_id, "external_id foi alterado!"

        print(f"\nCRITERIO #4-identity - PASS: provider e external_id imutaveis")

    def test_repeated_raw_update_keeps_one_transaction_and_no_audit(self, sessions):
        provider, external_id = get_first_transaction(sessions)
        for _ in range(2):
            upsert_raw_update(sessions, provider, external_id, "Synthetic update", "Synthetic category")
        with sessions() as db:
            assert db.query(Transaction).count() == 1
            assert GovernanceRepository().get_audit_log(db, provider, external_id) == []

    def test_governance_fields_not_in_allowed_raw(self):
        """
        Verifica que GOVERNANCE_FIELDS não estão em ALLOWED_RAW_FIELDS.
        Teste de contrato da separação.
        """
        from backend.domains.pierre.repository import IDENTITY_FIELDS, ALLOWED_RAW_FIELDS, GOVERNANCE_FIELDS

        intersection_identity_raw = IDENTITY_FIELDS & ALLOWED_RAW_FIELDS
        assert len(intersection_identity_raw) == 0, (
            f"IDENTITY_FIELDS e ALLOWED_RAW_FIELDS não devem se sobrepor: {intersection_identity_raw}"
        )

        intersection_gov_raw = GOVERNANCE_FIELDS & ALLOWED_RAW_FIELDS
        assert len(intersection_gov_raw) == 0, (
            f"GOVERNANCE_FIELDS e ALLOWED_RAW_FIELDS não devem se sobrepor: {intersection_gov_raw}"
        )

        intersection_gov_identity = GOVERNANCE_FIELDS & IDENTITY_FIELDS
        assert len(intersection_gov_identity) == 0, (
            f"GOVERNANCE_FIELDS e IDENTITY_FIELDS não devem se sobrepor: {intersection_gov_identity}"
        )

        print(f"\nCRITERIO #4-fields - PASS:")
        print(f"   IDENTITY_FIELDS:    {sorted(IDENTITY_FIELDS)}")
        print(f"   ALLOWED_RAW_FIELDS: {sorted(ALLOWED_RAW_FIELDS)}")
        print(f"   GOVERNANCE_FIELDS:  {sorted(GOVERNANCE_FIELDS)}")


class TestFullGovernanceFlow:
    """
    Critério #5, #6, #7, #8, #9 — fluxo completo de auditoria.
    PENDING → IGNORAR → ENTRADA+KNCR11 → ROLLBACK → IGNORAR
    """

    def test_full_audit_flow(self, sessions):
        """
        Testa o fluxo completo:
        CREATE_CLASSIFICATION → UPDATE_CLASSIFICATION → ROLLBACK
        """
        provider, external_id = get_first_transaction(sessions)
        tx_repo = TransactionRepository()
        gov_repo = GovernanceRepository()

        # PASSO 1: A fixture cria a transação em estado PENDING sem auditoria.
        tx = get_transaction(sessions, provider, external_id)
        assert tx.governance_status == "PENDING"
        assert tx.economic_classification is None

        # PASSO 2: CREATE_CLASSIFICATION — PENDING → IGNORAR
        db = sessions()
        try:
            tx_repo.classify(db, provider, external_id, "IGNORAR", reason="Evento 1 — IGNORAR")
            db.commit()
        finally:
            db.close()

        tx = get_transaction(sessions, provider, external_id)
        assert tx.governance_status == "CLASSIFIED"
        assert tx.economic_classification == "IGNORAR"

        # PASSO 3: UPDATE_CLASSIFICATION — IGNORAR → ENTRADA + KNCR11
        db = sessions()
        try:
            tx_repo.classify(db, provider, external_id, "ENTRADA",
                             investment_name="KNCR11", reason="Evento 2 — ENTRADA KNCR11")
            db.commit()
        finally:
            db.close()

        tx = get_transaction(sessions, provider, external_id)
        assert tx.economic_classification == "ENTRADA"
        assert tx.investment_name == "KNCR11"

        # PASSO 4: Verificar histórico (deve ter 2 eventos)
        db = sessions()
        try:
            history = gov_repo.get_audit_log(db, provider, external_id)
        finally:
            db.close()

        assert len(history) == 2, f"Esperado 2 eventos no histórico, obtido {len(history)}"

        # Evento mais recente: UPDATE_CLASSIFICATION
        latest_event = history[0]
        assert latest_event.action == "UPDATE_CLASSIFICATION", (
            f"Ação inesperada: {latest_event.action}"
        )

        # PASSO 5: ROLLBACK para o evento UPDATE_CLASSIFICATION (ENTRADA+KNCR11)
        # Isso restaura o estado BEFORE desse evento, que é IGNORAR (CLASSIFIED)
        # O evento[0] é o mais recente = UPDATE_CLASSIFICATION (ENTRADA+KNCR11)
        rollback_event_id = history[0].id  # UPDATE_CLASSIFICATION — before é IGNORAR
        db = sessions()
        try:
            gov_repo.rollback_to_event(db, provider, external_id,
                                        rollback_event_id, reason="Evento 3 — rollback para IGNORAR")
            db.commit()
        finally:
            db.close()

        # Verificar estado final — deve ser IGNORAR (CLASSIFIED, não PENDING)
        tx_final = get_transaction(sessions, provider, external_id)
        assert tx_final.governance_status == "CLASSIFIED", (
            f"Após rollback deveria ser CLASSIFIED: {tx_final.governance_status}. "
            "O rollback restaura o before_json do evento UPDATE (que era IGNORAR/CLASSIFIED)."
        )
        assert tx_final.economic_classification == "IGNORAR", (
            f"Após rollback deveria ser IGNORAR: {tx_final.economic_classification}"
        )

        # Verificar que o rollback criou novo evento de auditoria
        db = sessions()
        try:
            final_history = gov_repo.get_audit_log(db, provider, external_id)
        finally:
            db.close()

        assert len(final_history) == 3, "Rollback deve gerar uma terceira entrada no audit log"
        rollback_event = final_history[0]  # mais recente
        assert rollback_event.action == "ROLLBACK", (
            f"Evento de rollback deve ter action=ROLLBACK: {rollback_event.action}"
        )

        print(f"\nFLUXO COMPLETO DE AUDITORIA - PASS:")
        print(f"   Eventos gerados: {len(final_history)}")
        for ev in final_history[:3]:
            print(f"   - id={ev.id} action={ev.action}")
        print(f"   Estado final: status={tx_final.governance_status}, classificacao={tx_final.economic_classification}")
