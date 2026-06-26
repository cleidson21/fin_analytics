from pydantic import BaseModel
from typing import Optional

class TransactionDTO(BaseModel):
    id: str
    descricao: Optional[str] = None
    categoria: Optional[str] = None
    macro_categoria: str = "Outros"
    parcelamento: str = ""
    observacao: Optional[str] = None
    data_transacao: Optional[str] = None
    valor: Optional[float] = None
    valor_cents: Optional[int] = None
