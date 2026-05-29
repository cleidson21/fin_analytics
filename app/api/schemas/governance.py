from decimal import Decimal

from pydantic import BaseModel


class QuarantineTransaction(BaseModel):
    data: str
    descricao_original: str
    valor: Decimal
    identificador_externo: str | None