import pytest
from decimal import Decimal
from datetime import date
from backend.domains.investments.parsers.csv_parser import CSVTradeParser
from backend.domains.investments.import_report import ImportReport
from backend.domains.investments.dto import TradeType

def test_csv_parser_valid():
    csv_content = b"Ticker,Data,Tipo,Quantidade,Preco,Corretora\nPETR4,2023-01-10,COMPRA,100,25.50,XP\nVALE3,2023-01-15,VENDA,50,70.00,NU"
    parser = CSVTradeParser()
    report = ImportReport(source="CEI", file_name="test.csv")
    trades = parser.parse(csv_content, "test.csv", report)
    
    assert len(trades) == 2
    assert report.rows_parsed == 2
    assert len(report.errors) == 0
    
    t1 = trades[0]
    assert t1.ticker == "PETR4"
    assert t1.trade_date == date(2023, 1, 10)
    assert t1.operation_type == TradeType.BUY
    assert t1.quantity == Decimal('100')
    assert t1.unit_price == Decimal('25.50')
    assert t1.broker == "XP"

def test_csv_parser_invalid_missing_fields():
    csv_content = b"Ticker,Data,Tipo,Quantidade,Preco,Corretora\nPETR4,,COMPRA,100,25.50,XP"
    parser = CSVTradeParser()
    report = ImportReport(source="CEI", file_name="test.csv")
    trades = parser.parse(csv_content, "test.csv", report)
    
    assert len(trades) == 0
    assert len(report.errors) == 1
    assert "obrigatórios" in report.errors[0].message
