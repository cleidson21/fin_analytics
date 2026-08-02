import pytest
import os
from decimal import Decimal
from datetime import date
from unittest.mock import patch, mock_open

from backend.domains.imports.dto import CanonicalFinancialEvent, EventTypeEnum
from backend.domains.imports.readers.myprofit_csv import MyProfitProventosReader
from backend.domains.imports.validators.myprofit_proventos import MyProfitProventosValidator
from backend.domains.imports.parsers.myprofit_proventos import MyProfitProventosParser, MyProfitProventosRowDTO
from backend.domains.imports.normalizers.myprofit_proventos import MyProfitProventosNormalizer
from backend.domains.imports.pipelines.myprofit_proventos import MyProfitProventosPipeline

def test_reader_source_system():
    reader = MyProfitProventosReader()
    assert reader.source_system == "MYPROFIT"

def test_validator_success():
    validator = MyProfitProventosValidator()
    doc = type('obj', (object,), {'content': [{"Ativo": "X", "Recebido": "Y", "Data pgto.": "Z", "Cotas": "W"}]})
    assert validator.validate(doc) == True

def test_validator_failure():
    validator = MyProfitProventosValidator()
    doc = type('obj', (object,), {'content': [{"Ativo": "X", "Recebido": "Y"}]}) # Missing columns
    assert validator.validate(doc) == False

def test_parser_success():
    parser = MyProfitProventosParser()
    doc = type('obj', (object,), {
        'content': [{
            "Ativo": "KLBN4",
            "Recebido": "R$ 2,59",
            "Data pgto.": "12/11/2026",
            "Cotas": "57"
        }],
        'filename': 'test.csv'
    })
    
    dtos = parser.parse(doc)
    assert len(dtos) == 1
    assert dtos[0].ativo == "KLBN4"
    assert dtos[0].recebido == Decimal("2.59")
    assert dtos[0].data_pgto == date(2026, 11, 12)
    assert dtos[0].cotas == Decimal("57")

def test_parser_invalid_amount_and_date():
    parser = MyProfitProventosParser()
    doc = type('obj', (object,), {
        'content': [{
            "Ativo": "KLBN4",
            "Recebido": "invalid",
            "Data pgto.": "99/99/9999",
            "Cotas": "57"
        }],
        'filename': 'test.csv'
    })
    dtos = parser.parse(doc)
    assert len(dtos) == 0 # Ignored correctly

def test_normalizer_success():
    normalizer = MyProfitProventosNormalizer()
    dtos = [MyProfitProventosRowDTO(
        ativo="KLBN4",
        recebido=Decimal("2.59"),
        data_pgto=date(2026, 11, 12),
        cotas=Decimal("57")
    )]
    
    events = normalizer.normalize(dtos, "dummy_hash")
    
    assert len(events) == 1
    event = events[0]
    assert event.source_system == "MYPROFIT"
    assert event.event_type == EventTypeEnum.DIVIDEND
    assert event.amount == Decimal("2.59")
    assert event.asset == "KLBN4"
    assert event.quantity == Decimal("57")

def test_pipeline_catches_exception():
    pipeline = MyProfitProventosPipeline()
    # Mocking reader to raise exception
    with patch.object(pipeline.reader, 'read', side_effect=Exception("Disk error")):
        success, raw, canonical = pipeline.execute("fake.csv")
        assert not success
        assert canonical == []
