from typing import List
from pydantic import BaseModel
from decimal import Decimal, InvalidOperation
import logging
from datetime import datetime
from backend.domains.imports.dto import RawDocument

logger = logging.getLogger(__name__)

class NubankContaRowDTO(BaseModel):
    """Representação intermediária fortemente tipada da linha do Nubank Conta."""
    data: datetime
    valor: Decimal
    identificador: str
    descricao: str

class NubankContaParser:
    """Parser responsável por converter dict bruto em DTOs intermediários."""
    
    def parse(self, doc: RawDocument) -> List[NubankContaRowDTO]:
        parsed_rows = []
        for i, row in enumerate(doc.content):
            date_str = str(row.get("Data", ""))
            valor_str = str(row.get("Valor", ""))
            
            try:
                dt = datetime.strptime(date_str, "%d/%m/%Y")
                # Pandas converts empty cells to NaN which becomes "nan" string
                if valor_str.lower() == "nan":
                    raise ValueError("Valor vazio ou NaN")
                val = Decimal(valor_str)
            except (ValueError, InvalidOperation) as e:
                logger.warning(f"Erro ao converter linha {i} do arquivo {doc.filename}: {e}. Linha ignorada.")
                continue
            
            parsed_rows.append(NubankContaRowDTO(
                data=dt,
                valor=val,
                identificador=str(row.get("Identificador", "")),
                descricao=str(row.get("Descrição", ""))
            ))
        return parsed_rows
