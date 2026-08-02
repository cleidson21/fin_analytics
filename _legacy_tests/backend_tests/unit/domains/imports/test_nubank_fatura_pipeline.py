import pytest
from decimal import Decimal
from datetime import datetime, timezone
from backend.domains.imports.dto import RawDocument, EventTypeEnum
from backend.domains.imports.validators.nubank_fatura import NubankFaturaValidator
from backend.domains.imports.parsers.nubank_fatura import NubankFaturaParser
from backend.domains.imports.normalizers.nubank_fatura import NubankFaturaNormalizer
from backend.domains.imports.pipelines.nubank_fatura import NubankFaturaPipeline

def get_mock_raw_document():
    return RawDocument(
        source="NUBANK_FATURA_CSV",
        filename="test.csv",
        mime_type="text/csv",
        encoding="utf-8",
        parser_version="1.0.0",
        metadata={},
        content=[
            {"date": "2025-04-30", "title": "Mp *Loja Teste", "amount": "270,00"},
            {"date": "2025-04-06", "title": "Pagamento recebido", "amount": "- 3.077,10"}
        ],
        document_hash="hash",
        created_at=datetime.now(timezone.utc)
    )

def test_validator_success():
    validator = NubankFaturaValidator()
    doc = get_mock_raw_document()
    validator.validate(doc)

def test_validator_missing_column():
    validator = NubankFaturaValidator()
    doc = get_mock_raw_document()
    doc.content = [{"date": "2025-04-30", "title": "Mp *Loja Teste"}] # Missing amount
    with pytest.raises(ValueError, match="Colunas obrigatórias ausentes"):
        validator.validate(doc)

def test_validator_invalid_date_fatura():
    validator = NubankFaturaValidator()
    doc = get_mock_raw_document()
    doc.content[0]["date"] = "invalid-date"
    with pytest.raises(ValueError, match="Formato de data inválido na linha 1: invalid-date"):
        validator.validate(doc)

def test_parser_success():
    parser = NubankFaturaParser()
    doc = get_mock_raw_document()
    parsed = parser.parse(doc)
    assert len(parsed) == 2
    assert parsed[0].valor == Decimal("270.00")
    assert parsed[1].valor == Decimal("-3077.10")

def test_normalizer_success():
    parser = NubankFaturaParser()
    normalizer = NubankFaturaNormalizer()
    doc = get_mock_raw_document()
    
    parsed = parser.parse(doc)
    events = normalizer.normalize(parsed, doc.document_hash)
    
    assert len(events) == 2
    assert events[0].source_system == "NUBANK"
    assert events[0].event_type == EventTypeEnum.CREDIT_EXPENSE
    assert events[0].amount == Decimal("270.00")
    assert events[1].normalized_description == "Pagamento de Fatura"
    assert events[1].amount == Decimal("-3077.10")

def test_parser_invalid_date_dropped():
    parser = NubankFaturaParser()
    doc = get_mock_raw_document()
    doc.content.append({"date": "invalid", "title": "Teste", "amount": "10,00"})
    parsed = parser.parse(doc)
    assert len(parsed) == 2

def test_parser_invalid_amount_dropped():
    parser = NubankFaturaParser()
    doc = get_mock_raw_document()
    doc.content.append({"date": "2025-05-01", "title": "Teste", "amount": "invalid"})
    parsed = parser.parse(doc)
    assert len(parsed) == 2

def test_pipeline_catches_exception(monkeypatch):
    pipeline = NubankFaturaPipeline()
    def mock_read(*args, **kwargs):
        raise RuntimeError("Mock error")
    monkeypatch.setattr(pipeline.reader, "read", mock_read)
    
    with pytest.raises(RuntimeError, match="Mock error"):
        pipeline.execute("dummy.csv")
