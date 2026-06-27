from typing import List
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from backend.domains.imports.dto import RawDocument

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
        for row in doc.content:
            date_str = str(row["Data"])
            # Format is DD/MM/YYYY
            dt = datetime.strptime(date_str, "%d/%m/%Y")
            val = Decimal(str(row["Valor"]))
            
            parsed_rows.append(NubankContaRowDTO(
                data=dt,
                valor=val,
                identificador=str(row["Identificador"]),
                descricao=str(row["Descrição"])
            ))
        return parsed_rows
