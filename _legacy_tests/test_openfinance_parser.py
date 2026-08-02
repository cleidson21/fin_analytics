import pytest
from decimal import Decimal
from datetime import date
from backend.domains.investments.parsers.open_finance_parser import OpenFinanceParser
from backend.domains.investments.import_report import ImportReport
from backend.domains.investments.dto import TradeType

def test_openfinance_parser_valid():
    json_content = b"""
    [
        {
            "asset": "WEGE3",
            "transactionDate": "2023-08-20T10:00:00Z",
            "quantity": 200,
            "unitPrice": 15.00,
            "transactionType": "BUY",
            "institutionName": "NU"
        }
    ]
    """
    parser = OpenFinanceParser()
    report = ImportReport(source="OPEN_FINANCE", file_name="test.json")
    trades = parser.parse(json_content, "test.json", report)
    
    assert len(trades) == 1
    t1 = trades[0]
    assert t1.ticker == "WEGE3"
    assert t1.trade_date == date(2023, 8, 20)
    assert t1.quantity == Decimal('200')
    assert t1.unit_price == Decimal('15.00')
    assert t1.operation_type == TradeType.BUY

def test_openfinance_parser_invalid():
    json_content = b"""
    [
        {
            "asset": "WEGE3",
            "quantity": 200,
            "unitPrice": 15.00
        }
    ]
    """
    parser = OpenFinanceParser()
    report = ImportReport(source="OPEN_FINANCE", file_name="test.json")
    trades = parser.parse(json_content, "test.json", report)
    
    assert len(trades) == 0
    assert len(report.errors) == 1
