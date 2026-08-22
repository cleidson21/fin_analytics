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
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Ajuste de path para importar o backend como módulo
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.domains.pierre.repository import TransactionRepository, GovernanceRepository
from backend.database.session import SessionLocal

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_first_transaction():
    """Retorna (provider, external_id) da primeira transação no banco."""
    db = SessionLocal()
    try:
        from backend.domains.pierre.models import Transaction
        tx = db.query(Transaction).first()
        if tx is None:
            pytest.skip("Nenhuma transação no banco — rode o sync primeiro.")
        return tx.provider, tx.external_id
    finally:
        db.close()


def get_transaction(provider: str, external_id: str):
    """Retorna o objeto Transaction do banco."""
    db = SessionLocal()
    try:
        repo = TransactionRepository()
        return repo.get_by_external_id(db, provider, external_id)
    finally:
        db.close()


def classify_transaction(provider: str, external_id: str, classification: str, reason: str):
    """Classifica a transação e retorna o objeto atualizado."""
    db = SessionLocal()
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


def upsert_raw_update(provider: str, external_id: str, new_description: str, new_category: str):
    """
    Simula o que o sync faz: tenta atualizar campos RAW.
    Usa upsert() do TransactionRepository (mesmo método usado pelo pipeline).
    """
    db = SessionLocal()
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
            "amount": -42.00,
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

    def test_classify_then_raw_update_preserves_governance(self):
        """
        Fluxo completo:
        1. Obter transação existente
        2. Classificar como IGNORAR
        3. Simular sync (atualizar campos RAW via upsert)
        4. Verificar que governance_status e economic_classification foram preservados
        5. Verificar que description/category foram atualizados (RAW pode mudar)
        """
        provider, external_id = get_first_transaction()

        # PASSO 1: Classificar
        classify_transaction(
            provider, external_id,
            classification="IGNORAR",
            reason="Teste #4 — classificar antes do sync"
        )

        # Verificar estado ANTES do sync
        tx_before = get_transaction(provider, external_id)
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
        upsert_raw_update(provider, external_id, new_description, new_category)

        # PASSO 3: Verificar APÓS o sync
        tx_after = get_transaction(provider, external_id)
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

    def test_identity_fields_not_changed(self):
        """
        IDENTITY_FIELDS (provider, external_id) nunca podem mudar.
        """
        provider, external_id = get_first_transaction()

        # Tentar atualizar com campos extras via upsert (provider/external_id são identity)
        db = SessionLocal()
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

        tx = get_transaction(provider, external_id)
        assert tx is not None
        assert tx.provider == provider, "provider foi alterado!"
        assert tx.external_id == external_id, "external_id foi alterado!"

        print(f"\nCRITERIO #4-identity - PASS: provider e external_id imutaveis")

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

    def test_full_audit_flow(self):
        """
        Testa o fluxo completo:
        CREATE_CLASSIFICATION → UPDATE_CLASSIFICATION → ROLLBACK
        """
        provider, external_id = get_first_transaction()
        tx_repo = TransactionRepository()
        gov_repo = GovernanceRepository()

        # PASSO 1: Garantir estado PENDING
        db = SessionLocal()
        try:
            from backend.domains.pierre.models import Transaction
            tx = db.query(Transaction).filter(
                Transaction.provider == provider,
                Transaction.external_id == external_id
            ).first()
            # Reset para PENDING para garantir estado inicial limpo
            tx.governance_status = "PENDING"
            tx.economic_classification = None
            tx.investment_name = None
            tx.notes = None
            db.commit()
        finally:
            db.close()

        # PASSO 2: CREATE_CLASSIFICATION — PENDING → IGNORAR
        db = SessionLocal()
        try:
            tx_repo.classify(db, provider, external_id, "IGNORAR", reason="Evento 1 — IGNORAR")
            db.commit()
        finally:
            db.close()

        tx = get_transaction(provider, external_id)
        assert tx.governance_status == "CLASSIFIED"
        assert tx.economic_classification == "IGNORAR"

        # PASSO 3: UPDATE_CLASSIFICATION — IGNORAR → ENTRADA + KNCR11
        db = SessionLocal()
        try:
            tx_repo.classify(db, provider, external_id, "ENTRADA",
                             investment_name="KNCR11", reason="Evento 2 — ENTRADA KNCR11")
            db.commit()
        finally:
            db.close()

        tx = get_transaction(provider, external_id)
        assert tx.economic_classification == "ENTRADA"
        assert tx.investment_name == "KNCR11"

        # PASSO 4: Verificar histórico (deve ter 2 eventos)
        db = SessionLocal()
        try:
            history = gov_repo.get_audit_log(db, provider, external_id)
            # Filtra apenas eventos desta sequência (pode haver eventos anteriores)
            recent = history[:2]  # os mais recentes primeiro
        finally:
            db.close()

        assert len(history) >= 2, f"Esperado >= 2 eventos no histórico, obtido {len(history)}"

        # Evento mais recente: UPDATE_CLASSIFICATION
        latest_event = history[0]
        assert latest_event.action in ("UPDATE_CLASSIFICATION", "CREATE_CLASSIFICATION"), (
            f"Ação inesperada: {latest_event.action}"
        )

        # PASSO 5: ROLLBACK para o evento UPDATE_CLASSIFICATION (ENTRADA+KNCR11)
        # Isso restaura o estado BEFORE desse evento, que é IGNORAR (CLASSIFIED)
        # O evento[0] é o mais recente = UPDATE_CLASSIFICATION (ENTRADA+KNCR11)
        rollback_event_id = history[0].id  # UPDATE_CLASSIFICATION — before é IGNORAR
        db = SessionLocal()
        try:
            gov_repo.rollback_to_event(db, provider, external_id,
                                        rollback_event_id, reason="Evento 3 — rollback para IGNORAR")
            db.commit()
        finally:
            db.close()

        # Verificar estado final — deve ser IGNORAR (CLASSIFIED, não PENDING)
        tx_final = get_transaction(provider, external_id)
        assert tx_final.governance_status == "CLASSIFIED", (
            f"Após rollback deveria ser CLASSIFIED: {tx_final.governance_status}. "
            "O rollback restaura o before_json do evento UPDATE (que era IGNORAR/CLASSIFIED)."
        )
        assert tx_final.economic_classification == "IGNORAR", (
            f"Após rollback deveria ser IGNORAR: {tx_final.economic_classification}"
        )

        # Verificar que o rollback criou novo evento de auditoria
        db = SessionLocal()
        try:
            final_history = gov_repo.get_audit_log(db, provider, external_id)
        finally:
            db.close()

        assert len(final_history) >= 3, "Rollback deve gerar nova entrada no audit log"
        rollback_event = final_history[0]  # mais recente
        assert rollback_event.action == "ROLLBACK", (
            f"Evento de rollback deve ter action=ROLLBACK: {rollback_event.action}"
        )

        print(f"\nFLUXO COMPLETO DE AUDITORIA - PASS:")
        print(f"   Eventos gerados: {len(final_history)}")
        for ev in final_history[:3]:
            print(f"   - id={ev.id} action={ev.action}")
        print(f"   Estado final: status={tx_final.governance_status}, classificacao={tx_final.economic_classification}")
