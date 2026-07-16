from pydantic import BaseModel, Field
from typing import List, Optional

class AdvisorRequestDTO(BaseModel):
    question: str

class AdvisorResponseDTO(BaseModel):
    answer: str
    sources: List[str]
    generated_at: str
    model: str
    latency: float
    tokens: int

class AdvisorContext(BaseModel):
    patrimonio_atual: float
    patrimonio_investido: float
    patrimonio_liquido: float
    dividendos_acumulados: float
    maior_posicao: Optional[str] = None
    menor_posicao: Optional[str] = None
    percentual_caixa: float
    indicadores_macro: dict
