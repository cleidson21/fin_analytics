import pandas as pd
import io
from typing import List, Tuple
from backend.domains.investments.import_report import ImportReport
from backend.domains.investments.parsers.csv_parser import CSVTradeParser
from backend.domains.investments.parsers.open_finance_parser import OpenFinanceParser
from backend.domains.investments.parsers.ofx_parser import OFXParser
from backend.domains.investments.dto import TradeDTO

class ParseService:
    def parse_content(self, content: bytes, filename: str, import_type: str, report: ImportReport) -> Tuple[List[TradeDTO], str]:
        trades = []
        parser_name = "UNKNOWN"
        if import_type.upper() == "CEI":
            try:
                df = pd.read_excel(io.BytesIO(content), sheet_name="Negociação")
                parser = CSVTradeParser()
                parser_name = "CSVTradeParser"
                trades = parser.parse(content, filename, report)
            except Exception:
                parser = CSVTradeParser()
                parser_name = "CSVTradeParser"
                trades = parser.parse(content, filename, report)
        elif import_type.upper() == "OPEN_FINANCE":
            parser = OpenFinanceParser()
            parser_name = "OpenFinanceParser"
            trades = parser.parse(content, filename, report)
        elif import_type.upper() == "OFX":
            parser = OFXParser()
            parser_name = "OFXParser"
            trades = parser.parse(content, filename, report)
        else:
            parser = CSVTradeParser()
            parser_name = "CSVTradeParser"
            trades = parser.parse(content, filename, report)
        return trades, parser_name
