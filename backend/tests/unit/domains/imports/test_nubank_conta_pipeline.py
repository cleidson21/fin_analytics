import pytest
from decimal import Decimal
from datetime import datetime, timezone
from backend.domains.imports.dto import RawDocument, EventTypeEnum
from backend.domains.imports.validators.nubank_conta import NubankContaValidator
from backend.domains.imports.parsers.nubank_conta import NubankContaParser
from backend.domains.imports.normalizers.nubank_conta import NubankContaNormalizer
from backend.domains.imports.pipelines.nubank_conta import NubankContaPipeline

def get_mock_raw_document():
    return RawDocument(
        source="NUBANK_CONTA_CSV",
        filename="test.csv",
        mime_type="text/csv",
        encoding="utf-8",
        parser_version="1.0.0",
        metadata={},
        content=[
            {"Data": "02/05/2025", "Valor": "-100.00", "Identificador": "uuid-1", "Descrição": "Dinheiro guardado"}
        ],
        document_hash="hash",
        created_at=datetime.now(timezone.utc)
    )

def test_validator_success():
    validator = NubankContaValidator()
    doc = get_mock_raw_document()
    validator.validate(doc) # should not raise

def test_validator_missing_column():
    validator = NubankContaValidator()
    doc = get_mock_raw_document()
    doc.content = [{"Data": "02/05/2025", "Valor": "-100.00", "Identificador": "uuid-1"}] # Missing Descrição
    with pytest.raises(ValueError, match="Colunas obrigatórias ausentes"):
        validator.validate(doc)

def test_validator_invalid_date():
    validator = NubankContaValidator()
    doc = get_mock_raw_document()
    doc.content[0]["Data"] = "invalid"
    with pytest.raises(ValueError, match="Formato de data inválido"):
        validator.validate(doc)

def test_parser_success():
    parser = NubankContaParser()
    doc = get_mock_raw_document()
    parsed = parser.parse(doc)
    assert len(parsed) == 1
    assert parsed[0].data.day == 2
    assert parsed[0].valor == Decimal("-100.00")
    assert parsed[0].identificador == "uuid-1"

def test_normalizer_success():
    parser = NubankContaParser()
    normalizer = NubankContaNormalizer()
    doc = get_mock_raw_document()
    
    parsed = parser.parse(doc)
    events = normalizer.normalize(parsed, doc.document_hash)
    
    assert len(events) == 1
    assert events[0].source_system == "NUBANK"
    assert events[0].event_type == EventTypeEnum.CASH_FLOW
    assert events[0].amount == Decimal("-100.00")
    assert events[0].external_uuid == "uuid-1"

def test_parser_invalid_date_dropped():
    parser = NubankContaParser()
    doc = get_mock_raw_document()
    doc.content.append({"Data": "99/99/9999", "Valor": "100.00", "Identificador": "uuid-2", "Descrição": "Teste"})
    parsed = parser.parse(doc)
    # The invalid line should be dropped without crashing
    assert len(parsed) == 1
    assert parsed[0].identificador == "uuid-1"

def test_parser_nan_amount_dropped():
    parser = NubankContaParser()
    doc = get_mock_raw_document()
    doc.content.append({"Data": "03/05/2025", "Valor": "NaN", "Identificador": "uuid-3", "Descrição": "Teste NaN"})
    parsed = parser.parse(doc)
    # The invalid line should be dropped
    assert len(parsed) == 1
    assert parsed[0].identificador == "uuid-1"

def test_pipeline_catches_exception(monkeypatch):
    pipeline = NubankContaPipeline()
    def mock_read(*args, **kwargs):
        raise RuntimeError("Mock error")
    monkeypatch.setattr(pipeline.reader, "read", mock_read)
    
    with pytest.raises(RuntimeError, match="Mock error"):
        pipeline.execute("dummy.csv")
