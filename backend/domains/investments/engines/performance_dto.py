from decimal import Decimal
from typing import List, Optional
from datetime import date
from pydantic import BaseModel

class CashFlow(BaseModel):
    """Representa um fluxo de caixa datado (aporte, retirada, dividendo, amortização)."""
    amount: Decimal         # Positivo = entrada, Negativo = saída
    flow_date: date
    flow_type: str          # "DEPOSIT", "WITHDRAWAL", "DIVIDEND", "AMORTIZATION"

class PerformanceMetrics(BaseModel):
    """Métricas de desempenho calculadas para um período ou portfólio."""
    # Retornos absolutos
    unrealized_gain: Decimal       # Ganho não realizado (custo vs mercado)
    realized_gain: Decimal         # Ganho realizado (de vendas históricas)
    total_gain: Decimal            # Total Gain = Unrealized + Realized
    dividends_received: Decimal    # Total de dividendos recebidos
    total_return: Decimal          # total_gain + dividends_received

    # Retornos percentuais
    unrealized_return_pct: Decimal
    realized_return_pct: Decimal
    total_return_pct: Decimal

    # Métricas de Yield
    yield_on_cost: Decimal         # Dividends / Cost Basis * 100

    # Rentabilidades anualizadas
    cagr: Decimal                  # Compound Annual Growth Rate
    annualized_return_pct: Decimal

    # Retornos por período (aproximados via média simples dos sub-períodos)
    monthly_return_pct: Decimal
    daily_return_pct: Decimal

    # Métricas avançadas
    mwr: Decimal                   # Money-Weighted Return (IRR aproximada pelo método Newton)
    twr: Decimal                   # Time-Weighted Return

class PerformanceSummary(BaseModel):
    """Wrapper completo do resultado da Performance Engine."""
    cost_basis: Decimal
    market_value: Decimal
    metrics: PerformanceMetrics
    holding_days: int
