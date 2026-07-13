import csv
import logging
from typing import List, Dict, Any
from datetime import datetime
from decimal import Decimal
import io
import hashlib

from backend.domains.investments.dto import TradeDTO, TradeType, AssetTypeEnum
from backend.domains.investments.import_report import ImportReport, ImportError, ImportWarning

logger = logging.getLogger(__name__)

class CSVParserException(Exception):
    pass

class CSVTradeParser:
    """
    Parser for CSV files (like Nubank or MyProfit formats).
    It extracts basic trades into TradeDTOs.
    """
    
    def parse(self, content: bytes, filename: str, report: ImportReport) -> List[TradeDTO]:
        try:
            # Decode content assuming UTF-8
            decoded = content.decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(decoded), delimiter=',')
        except Exception as e:
            report.errors.append(ImportError(message=f"Falha ao ler CSV: {str(e)}"))
            return []

        trades = []
        for i, row in enumerate(reader):
            report.rows_read += 1
            try:
                # We expect a simple standard structure or fallbacks for Nubank/MyProfit headers
                ticker = row.get('Ticker') or row.get('Ativo') or row.get('codigo_negociacao')
                if not ticker:
                    report.warnings.append(ImportWarning(message="Ticker não encontrado", row=i+1))
                    report.rows_parsed += 1
                    continue
                    
                date_str = row.get('Data') or row.get('data_negocio')
                qty_str = row.get('Quantidade') or row.get('quantidade')
                price_str = row.get('Preco') or row.get('preco_unitario') or row.get('Preço')
                broker = row.get('Corretora') or row.get('instituicao') or "Default Broker"
                type_str = row.get('Tipo') or row.get('tipo_movimentacao') or "COMPRA"

                if not date_str or not qty_str or not price_str:
                    report.errors.append(ImportError(message="Linha sem campos obrigatórios (Data, Quantidade ou Preço)", row=i+1))
                    report.rows_parsed += 1
                    continue

                trade_date = datetime.strptime(date_str, "%Y-%m-%d").date() if "-" in date_str else datetime.strptime(date_str, "%d/%m/%Y").date()
                qty = Decimal(str(qty_str).replace(',', '.'))
                price = Decimal(str(price_str).replace(',', '.'))
                total_val = qty * price
                
                op_type = TradeType.BUY if "compra" in type_str.lower() or "c" in type_str.lower() else TradeType.SELL

                # Create idempotency hash
                raw_str = f"{ticker}{date_str}{op_type.value}{qty}{price}{broker}".encode('utf-8')
                tx_hash = hashlib.md5(raw_str).hexdigest()

                trade = TradeDTO(
                    idempotency_hash=tx_hash,
                    operation_type=op_type,
                    trade_date=trade_date,
                    quantity=qty,
                    unit_price=price,
                    total_value=total_val,
                    source=filename,
                    ticker=ticker,
                    broker=broker,
                    metadata={"raw": dict(row)}
                )
                trades.append(trade)
                report.rows_parsed += 1
                report.rows_normalized += 1
                
            except Exception as e:
                report.errors.append(ImportError(message=f"Erro de formato: {str(e)}", row=i+1))
                report.rows_parsed += 1
                
        return trades
