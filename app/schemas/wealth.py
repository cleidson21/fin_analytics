from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class BenchmarkBase(BaseModel):
    reference_date: date
    type: str
    value_pct: float

class BenchmarkResponse(BenchmarkBase):
    id: str
    class Config:
        from_attributes = True

class PositionBase(BaseModel):
    ticker: str
    data_snapshot: date
    source: str
    quantidade: float
    preco_medio: float
    total_investido: float
    preco_atual: float
    total_atual: float
    ganho: float

class PositionResponse(PositionBase):
    import_run_id: str
    class Config:
        from_attributes = True

class DividendBase(BaseModel):
    id_economico: str
    source: str
    ticker: str
    tipo_evento: str
    data_pagamento: date
    valor_liquido: float

class DividendResponse(DividendBase):
    import_run_id: str
    class Config:
        from_attributes = True

class PortfolioEvolutionBase(BaseModel):
    reference_month: date
    patrimonio_cents: int

class PortfolioEvolutionResponse(PortfolioEvolutionBase):
    id: int
    import_run_id: str
    class Config:
        from_attributes = True
