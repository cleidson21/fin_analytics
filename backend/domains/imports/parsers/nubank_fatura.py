import re
import logging
from typing import List
from pydantic import BaseModel
from decimal import Decimal, InvalidOperation
from datetime import datetime
from backend.domains.imports.dto import RawDocument

logger = logging.getLogger(__name__)

class NubankFaturaRowDTO(BaseModel):
    """Representação intermediária fortemente tipada da linha da Fatura Nubank."""
    data: datetime
    titulo: str
    valor: Decimal

class NubankFaturaParser:
    """Parser responsável por converter dict bruto em DTOs intermediários."""
    
    def parse(self, doc: RawDocument) -> List[NubankFaturaRowDTO]:
        parsed_rows = []
        for i, row in enumerate(doc.content):
            date_str = str(row.get("date", ""))
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError as e:
                logger.warning(f"Linha {i+1} ignorada: Erro de data: '{date_str}'. Detalhe: {e}")
                continue
            
            raw_amount = str(row.get("amount", ""))
            val_str = raw_amount.replace(".", "").replace(",", ".")
            val_str = re.sub(r'[^0-9\.\-]', '', val_str)
            
            try:
                val = Decimal(val_str)
            except InvalidOperation as e:
                logger.warning(f"Linha {i+1} ignorada: Falha ao converter valor bruto '{raw_amount}' para Decimal. Erro original: {e}")
                continue
            
            parsed_rows.append(NubankFaturaRowDTO(
                data=dt,
                titulo=str(row.get("title", "")),
                valor=val
            ))
        return parsed_rows
