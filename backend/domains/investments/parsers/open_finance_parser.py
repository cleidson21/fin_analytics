import json
import logging
from typing import List
from datetime import datetime
from decimal import Decimal
import hashlib

from backend.domains.investments.dto import TradeDTO, TradeType
from backend.domains.investments.import_report import ImportReport, ImportError, ImportWarning

logger = logging.getLogger(__name__)

class OpenFinanceParser:
    """
    Parser for Open Finance JSON payloads.
    """
    
    def parse(self, content: bytes, filename: str, report: ImportReport) -> List[TradeDTO]:
        try:
            decoded = content.decode('utf-8')
            data = json.loads(decoded)
        except Exception as e:
            report.errors.append(ImportError(message=f"Falha ao ler JSON: {str(e)}"))
            return []

        # Open Finance typically returns an array under "data" or root array
        transactions = data.get("data", data) if isinstance(data, dict) else data
        if not isinstance(transactions, list):
            report.errors.append(ImportError(message="Estrutura JSON inválida. Esperado array."))
            return []

        trades = []
        for i, row in enumerate(transactions):
            report.rows_read += 1
            try:
                # Based on Open Finance Investment APIs
                ticker = row.get('ticker') or row.get('assetCode') or row.get('asset')
                if not ticker:
                    report.warnings.append(ImportWarning(message="Ticker não encontrado", row=i+1))
                    report.rows_parsed += 1
                    continue
                    
                date_str = row.get('transactionDate') or row.get('date')
                qty_val = row.get('quantity')
                price_val = row.get('unitPrice') or row.get('price')
                broker = row.get('institutionName') or row.get('broker') or "Open Finance Institution"
                type_str = row.get('transactionType') or "BUY"

                if not date_str or qty_val is None or price_val is None:
                    report.errors.append(ImportError(message="Linha sem campos obrigatórios (Data, Quantidade ou Preço)", row=i+1))
                    report.rows_parsed += 1
                    continue

                # Parse date
                try:
                    trade_date = datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
                except:
                    trade_date = datetime.strptime(date_str, "%Y-%m-%d").date()

                qty = Decimal(str(qty_val))
                price = Decimal(str(price_val))
                total_val = qty * price
                
                op_type = TradeType.BUY if type_str.upper() in ["BUY", "COMPRA"] else TradeType.SELL

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
                    source=f"OpenFinance:{filename}",
                    ticker=ticker,
                    broker=broker,
                    metadata={"raw": row}
                )
                trades.append(trade)
                report.rows_parsed += 1
                report.rows_normalized += 1
                
            except Exception as e:
                report.errors.append(ImportError(message=f"Erro de formato: {str(e)}", row=i+1))
                report.rows_parsed += 1
                
        return trades
