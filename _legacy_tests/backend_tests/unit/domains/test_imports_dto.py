import pytest
from datetime import datetime, date, timezone
from decimal import Decimal
from pydantic import ValidationError

from backend.domains.imports.dto import (
    EventTypeEnum,
    ImportStatusEnum,
    RawDocument,
    CanonicalFinancialEvent,
    ImportSessionDTO,
    ImportBatchDTO,
    ImportRunDTO,
    ImportAuditDTO,
    ImportRunStatistics
)

def test_raw_document_instantiation():
    doc = RawDocument(
        source="NUBANK",
        filename="extrato.csv",
        mime_type="text/csv",
        encoding="utf-8",
        parser_version="1.0.0",
        content="raw,csv,content",
        document_hash="abc123hash",
        created_at=datetime.now(timezone.utc)
    )
    assert doc.source == "NUBANK"
    assert doc.metadata == {}  # default_factory

def test_canonical_financial_event_valid_trade():
    event = CanonicalFinancialEvent(
        source_system="B3",
        source_type="XLSX",
        event_type=EventTypeEnum.TRADE,
        transaction_date=date(2026, 6, 25),
        description="COMPRA PETR4",
        normalized_description="Compra de Ativo",
        amount=Decimal("-1500.00"),
        currency="BRL",
        asset="PETR4",
        quantity=Decimal("100"),
        external_hash="hash123"
    )
    assert event.event_type == EventTypeEnum.TRADE
    assert event.asset == "PETR4"
    assert event.quantity == Decimal("100")

def test_canonical_financial_event_invalid_trade_missing_asset():
    with pytest.raises(ValidationError) as exc:
        CanonicalFinancialEvent(
            source_system="B3",
            source_type="XLSX",
            event_type=EventTypeEnum.TRADE,
            transaction_date=date(2026, 6, 25),
            description="COMPRA INVALIDA",
            normalized_description="Compra de Ativo",
            amount=Decimal("-1500.00"),
            currency="BRL"
        )
    assert "Eventos do tipo TRADE exigem 'asset' e 'quantity'" in str(exc.value)

def test_canonical_financial_event_invalid_credit_expense():
    with pytest.raises(ValidationError) as exc:
        CanonicalFinancialEvent(
            source_system="NUBANK",
            source_type="CSV",
            event_type=EventTypeEnum.CREDIT_EXPENSE,
            transaction_date=date(2026, 6, 25),
            description="iFood",
            normalized_description="Alimentação",
            amount=Decimal("-50.00"),
            currency="BRL"
        )
    assert "Eventos do tipo CREDIT_EXPENSE exigem 'credit_card'" in str(exc.value)

def test_import_session_dto():
    session = ImportSessionDTO(
        session_id="session-123",
        created_at=datetime.now(timezone.utc),
        user_id="user-1",
        files=["extrato.csv"],
        status=ImportStatusEnum.PENDING
    )
    assert session.status == ImportStatusEnum.PENDING

def test_import_batch_dto():
    doc = RawDocument(
        source="NUBANK", filename="a.csv", mime_type="text/csv", 
        encoding="utf-8", parser_version="1", content="a", 
        document_hash="h", created_at=datetime.now(timezone.utc)
    )
    batch = ImportBatchDTO(
        batch_id="batch-123",
        session_id="session-123",
        documents=[doc],
        validation_status=ImportStatusEnum.PROCESSING
    )
    assert len(batch.documents) == 1

def test_import_run_dto():
    run = ImportRunDTO(
        run_id="run-123",
        batch_id="batch-123",
        started_at=datetime.now(timezone.utc),
        statistics=ImportRunStatistics(total_processed=10, total_inserted=10)
    )
    assert run.statistics.total_processed == 10
    assert run.rollback_available is True

def test_import_audit_dto():
    audit = ImportAuditDTO(
        run_id="run-123",
        created=10,
        updated=2,
        ignored=0,
        conflicts=1,
        warnings=0,
        errors=0
    )
    assert audit.created == 10
    assert audit.conflicts == 1
