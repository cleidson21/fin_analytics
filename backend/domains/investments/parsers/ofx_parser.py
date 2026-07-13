import xml.etree.ElementTree as ET
import logging
from typing import List
from datetime import datetime
from decimal import Decimal
import hashlib

from backend.domains.investments.dto import TradeDTO, TradeType
from backend.domains.investments.import_report import ImportReport, ImportError, ImportWarning

logger = logging.getLogger(__name__)

class OFXParserException(Exception):
    pass

class OFXParser:
    """
    Parser for basic OFX (Open Financial Exchange) files.
    """
    
    def parse(self, content: bytes, filename: str, report: ImportReport) -> List[TradeDTO]:
        # Basic cleanup since many OFX files don't have strict XML roots or they have headers
        try:
            decoded = content.decode('utf-8', errors='ignore')
            # Extract only the SGML/XML part if there are OFX headers
            if "<OFX>" in decoded:
                xml_content = "<OFX>" + decoded.split("<OFX>")[1]
            else:
                xml_content = decoded
                
            # Quick & dirty fix for unclosed tags which is common in older OFX
            # This is a basic XML parse. For robust OFX parsing, we'd use ofxparse, 
            # but we'll stick to a native implementation for this Gate.
            # We'll just manually grep INVTRANLIST
            import re
            
            transactions = re.findall(r'<INVBANKTRAN>.*?</INVBANKTRAN>', xml_content, re.DOTALL)
            if not transactions:
                # Try standard BANKTRANLIST
                transactions = re.findall(r'<STMTTRN>.*?</STMTTRN>', xml_content, re.DOTALL)
                
            if not transactions:
                report.errors.append(ImportError(message="Nenhuma transação encontrada no arquivo OFX."))
                return []
                
        except Exception as e:
            report.errors.append(ImportError(message=f"Falha ao ler OFX: {str(e)}"))
            return []

        trades = []
        for i, tx_text in enumerate(transactions):
            report.rows_read += 1
            try:
                # Extract fields using regex
                def get_tag(tag):
                    match = re.search(f'<{tag}>(.*?)(?:</{tag}>|\n|<)', tx_text)
                    return match.group(1).strip() if match else None
                
                ticker = get_tag('NAME') or get_tag('MEMO')
                if not ticker:
                    report.warnings.append(ImportWarning(message="Ticker (NAME/MEMO) não encontrado", row=i+1))
                    report.rows_parsed += 1
                    continue
                    
                date_str = get_tag('DTPOSTED')
                amount_str = get_tag('TRNAMT')
                
                if not date_str or not amount_str:
                    report.errors.append(ImportError(message="Linha sem campos obrigatórios (DTPOSTED, TRNAMT)", row=i+1))
                    report.rows_parsed += 1
                    continue

                # OFX Date format: YYYYMMDDHHMMSS
                try:
                    trade_date = datetime.strptime(date_str[:8], "%Y%m%d").date()
                except:
                    report.errors.append(ImportError(message=f"Formato de data inválido: {date_str}", row=i+1))
                    report.rows_parsed += 1
                    continue
                    
                total_val = Decimal(amount_str)
                
                # If negative, it's a BUY (money left account to buy stock). If positive, SELL.
                if total_val < 0:
                    op_type = TradeType.BUY
                    total_val = abs(total_val)
                else:
                    op_type = TradeType.SELL

                # Since OFX bank transfers don't usually have quantity and price for stocks (unless INVBANKTRAN),
                # we'll assume qty=1 and unit_price=total_val for general compat, or extract if INVTRAN
                qty_str = get_tag('UNITS')
                price_str = get_tag('UNITPRICE')
                
                if qty_str and price_str:
                    qty = Decimal(qty_str)
                    price = Decimal(price_str)
                else:
                    qty = Decimal('1')
                    price = total_val
                
                broker = "Importação OFX"

                # Create idempotency hash
                raw_str = f"{ticker}{date_str}{op_type.value}{qty}{price}".encode('utf-8')
                tx_hash = hashlib.md5(raw_str).hexdigest()

                trade = TradeDTO(
                    idempotency_hash=tx_hash,
                    operation_type=op_type,
                    trade_date=trade_date,
                    quantity=abs(qty),
                    unit_price=abs(price),
                    total_value=abs(total_val),
                    source=f"OFX:{filename}",
                    ticker=ticker,
                    broker=broker,
                    metadata={"raw": tx_text}
                )
                trades.append(trade)
                report.rows_parsed += 1
                report.rows_normalized += 1
                
            except Exception as e:
                report.errors.append(ImportError(message=f"Erro de formato: {str(e)}", row=i+1))
                report.rows_parsed += 1
                
        return trades
