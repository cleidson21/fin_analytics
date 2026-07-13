import pytest
from decimal import Decimal
from datetime import date
from backend.domains.investments.parsers.ofx_parser import OFXParser
from backend.domains.investments.import_report import ImportReport
from backend.domains.investments.dto import TradeType

def test_ofx_parser_valid():
    ofx_content = b"""
    <OFX>
        <INVBANKTRAN>
            <STMTTRN>
                <DTPOSTED>20230510120000</DTPOSTED>
                <TRNAMT>-2550.00</TRNAMT>
                <NAME>PETR4</NAME>
            </STMTTRN>
            <UNITS>100</UNITS>
            <UNITPRICE>25.50</UNITPRICE>
        </INVBANKTRAN>
    </OFX>
    """
    parser = OFXParser()
    report = ImportReport(source="OFX", file_name="test.ofx")
    trades = parser.parse(ofx_content, "test.ofx", report)
    
    assert len(trades) == 1
    assert len(report.errors) == 0
    t1 = trades[0]
    assert t1.ticker == "PETR4"
    assert t1.operation_type == TradeType.BUY
    assert t1.trade_date == date(2023, 5, 10)
    assert t1.quantity == Decimal('100')
    assert t1.unit_price == Decimal('25.50')

def test_ofx_parser_invalid():
    ofx_content = b"<OFX><INVBANKTRAN><STMTTRN><DTPOSTED>invalid</DTPOSTED><TRNAMT>50.0</TRNAMT><NAME>VALE3</NAME></STMTTRN></INVBANKTRAN></OFX>"
    parser = OFXParser()
    report = ImportReport(source="OFX", file_name="test.ofx")
    trades = parser.parse(ofx_content, "test.ofx", report)
    
    assert len(trades) == 0
    assert len(report.errors) == 1
    assert "Formato de data inválido" in report.errors[0].message
