from pydantic import BaseModel
from typing import Optional


class DividendHistory(BaseModel):
    month: str
    amount_received: str
    amount_received_value: Optional[float] = None
    amount_dividend: Optional[str] = None
    amount_dividend_value: Optional[float] = None
    amount_jcp: Optional[str] = None
    amount_jcp_value: Optional[float] = None
    amount_rendimento: Optional[str] = None
    amount_rendimento_value: Optional[float] = None


class AssetAllocation(BaseModel):
    asset_class: str
    current_total: str
    current_total_value: Optional[float] = None


class NetWorthEvolution(BaseModel):
    month: str
    net_worth: str
    net_worth_value: Optional[float] = None


class PositionDetail(BaseModel):
    ticker: str
    asset_class: str
    asset_subclass: str
    quantidade: str
    preco_medio: str
    valor_investido: str
    valor_atual: str
    ganho: str
    peso_percentual: str
    
    quantidade_value: Optional[float] = None
    preco_medio_value: Optional[float] = None
    valor_investido_value: Optional[float] = None
    valor_atual_value: Optional[float] = None
    ganho_value: Optional[float] = None
    peso_percentual_value: Optional[float] = None


class DividendBreakdown(BaseModel):
    ticker: str
    total_recebido: str
    quantidade_eventos: int
    primeiro_recebimento: str
    ultimo_recebimento: str
    total_recebido_value: Optional[float] = None


class PortfolioEvolutionPoint(BaseModel):
    month: str
    patrimonio: str
    patrimonio_value: float
    compras: str
    compras_value: float
    vendas: str
    vendas_value: float
    proventos: str
    proventos_value: float
    rentabilidade_mensal_pct: float
    rentabilidade_acumulada_pct: float
    ibov_mensal_pct: float
    ibov_acumulado_pct: float
    cdi_mensal_pct: float
    cdi_acumulado_pct: float
    ipca_mensal_pct: float
    ipca_acumulado_pct: float
    ifix_mensal_pct: float
    ifix_acumulado_pct: float
    sp500_mensal_pct: float
    sp500_acumulado_pct: float
    idiv_mensal_pct: float
    idiv_acumulado_pct: float


class PortfolioEvolutionSummary(BaseModel):
    patrimonio_atual: str
    patrimonio_atual_value: float
    rentabilidade_acumulada: float
    proventos_totais: float
    compras_totais: float
    vendas_totais: float
    ibov_acumulado_pct: float
    cdi_acumulado_pct: float
    alpha_vs_ibov: float
    alpha_vs_cdi: float