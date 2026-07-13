import logging
import re
from typing import List
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from pydantic import BaseModel
from backend.domains.imports.dto import RawDocument

logger = logging.getLogger(__name__)

class MyProfitProventosRowDTO(BaseModel):
    ativo: str
    recebido: Decimal
    data_pgto: date
    cotas: Decimal

class MyProfitProventosParser:
    """Parser responsável por converter dict bruto de proventos em DTOs intermediários."""
    
    def parse(self, doc: RawDocument) -> List[MyProfitProventosRowDTO]:
        parsed_rows = []
        for i, row in enumerate(doc.content):
            ativo_str = str(row.get("Ativo", "")).strip()
            recebido_str = str(row.get("Recebido", "")).strip()
            data_pgto_str = str(row.get("Data pgto.", "")).strip()
            cotas_str = str(row.get("Cotas", "")).strip()
            
            try:
                if not ativo_str or not recebido_str or not data_pgto_str or not cotas_str:
                    raise ValueError("Campos obrigatórios ausentes")
                
                # Tratar Pandas NaN (mesmo modelo da EA3-12)
                if str(ativo_str).lower() == "nan" or str(data_pgto_str).lower() == "nan":
                    raise ValueError("Valor vazio ou NaN gerado pelo pandas")
                
                # Converter data_pgto (formato %d/%m/%Y)
                dt = datetime.strptime(data_pgto_str, "%d/%m/%Y").date()
                
                # Converter Recebido ("R$ 2,59" -> 2.59)
                rec_clean = re.sub(r'[^\d,-]', '', recebido_str)
                rec_clean = rec_clean.replace(',', '.')
                recebido = Decimal(rec_clean)
                
                # Converter Cotas (pode usar ponto ou vírgula, e.g. "0.094")
                cotas_clean = cotas_str.replace(',', '.')
                cotas = Decimal(cotas_clean)
                
                parsed_rows.append(MyProfitProventosRowDTO(
                    ativo=ativo_str,
                    recebido=recebido,
                    data_pgto=dt,
                    cotas=cotas
                ))
            except (ValueError, InvalidOperation, TypeError) as e:
                logger.warning(f"Erro ao converter linha {i} do arquivo {doc.filename}: {e}. Linha ignorada.")
                continue
                
        return parsed_rows
