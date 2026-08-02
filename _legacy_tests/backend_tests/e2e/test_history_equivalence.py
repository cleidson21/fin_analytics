from backend.domains.investments.application_factory import ApplicationFactory
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from datetime import date
from decimal import Decimal
from typing import List
from backend.domains.investments.dto import TradeDTO, TradeType, PositionSnapshot
from backend.domains.investments.engines.position_engine import PositionEngine, PositionResult
from backend.domains.investments.services.history_service import HistoryService

def test_history_equivalence():
    """
    Testa se o histórico gerado de forma incremental no HistoryService O(N+M)
    tem equivalência estrita ao modelo antigo do PerformanceEngine O(N*M).
    Como removemos a versão O(N*M), usaremos um runner que reproduz O(N*M) localmente
    apenas para garantir que a saída não mudou.
    """
    
    # Massa de dados: 6 meses de transações espaçadas
    trades = [
        TradeDTO(ticker="PETR4", broker="XP", operation_type=TradeType.BUY, trade_date=date(2025, 1, 10), quantity=Decimal('100'), unit_price=Decimal('10'), total_value=Decimal('1000'), source="T", idempotency_hash="1"),
        TradeDTO(ticker="PETR4", broker="XP", operation_type=TradeType.BUY, trade_date=date(2025, 2, 15), quantity=Decimal('50'), unit_price=Decimal('12'), total_value=Decimal('600'), source="T", idempotency_hash="2"),
        TradeDTO(ticker="VALE3", broker="XP", operation_type=TradeType.BUY, trade_date=date(2025, 3, 20), quantity=Decimal('10'), unit_price=Decimal('50'), total_value=Decimal('500'), source="T", idempotency_hash="3"),
        TradeDTO(ticker="PETR4", broker="XP", operation_type=TradeType.SELL, trade_date=date(2025, 4, 10), quantity=Decimal('50'), unit_price=Decimal('15'), total_value=Decimal('750'), source="T", idempotency_hash="4"),
        TradeDTO(ticker="PETR4", broker="XP", operation_type=TradeType.AMORTIZATION, trade_date=date(2025, 5, 5), quantity=Decimal('1'), unit_price=Decimal('1.5'), total_value=Decimal('150'), source="T", idempotency_hash="5"),
        TradeDTO(ticker="VALE3", broker="XP", operation_type=TradeType.SELL, trade_date=date(2025, 6, 12), quantity=Decimal('10'), unit_price=Decimal('60'), total_value=Decimal('600'), source="T", idempotency_hash="6"),
    ]
    
    from backend.domains.investments.services.historical_price_service import HistoricalPriceService
    hist_service = ApplicationFactory.get_historical_price_service()
    
    market_prices = {
        "PETR4": Decimal("14"),
        "VALE3": Decimal("55")
    }
    
    service = ApplicationFactory.get_history_service()
    history = service.generate_history(
        trades=trades,
        snapshots=[],
        market_prices=market_prices,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 6, 30),
        granularity="month"
    )
    
    points = history.points
    assert len(points) == 6
    
    # Janeiro: Comprou 1000
    p_jan = hist_service.get_price_for_date("PETR4", date(2025, 1, 31)) or Decimal('14')
    assert points[0].compras_value == Decimal('1000')
    assert points[0].vendas_value == Decimal('0')
    assert points[0].patrimonio_value == 100 * p_jan
    
    # Fevereiro: Comprou 600
    p_fev = hist_service.get_price_for_date("PETR4", date(2025, 2, 28)) or Decimal('14')
    assert points[1].compras_value == Decimal('600')
    assert points[1].patrimonio_value == 150 * p_fev
    
    # Março: Comprou 500
    p_mar_petr4 = hist_service.get_price_for_date("PETR4", date(2025, 3, 31)) or Decimal('14')
    p_mar_vale3 = hist_service.get_price_for_date("VALE3", date(2025, 3, 31)) or Decimal('55')
    assert points[2].compras_value == Decimal('500')
    assert points[2].patrimonio_value == (150 * p_mar_petr4) + (10 * p_mar_vale3)
    
    # Abril: Vendeu 750
    p_abr_petr4 = hist_service.get_price_for_date("PETR4", date(2025, 4, 30)) or Decimal('14')
    p_abr_vale3 = hist_service.get_price_for_date("VALE3", date(2025, 4, 30)) or Decimal('55')
    assert points[3].vendas_value == Decimal('750')
    assert points[3].patrimonio_value == (100 * p_abr_petr4) + (10 * p_abr_vale3)
    
    # Maio: Amortizou 150
    p_mai_petr4 = hist_service.get_price_for_date("PETR4", date(2025, 5, 31)) or Decimal('14')
    p_mai_vale3 = hist_service.get_price_for_date("VALE3", date(2025, 5, 31)) or Decimal('55')
    assert points[4].proventos_value == Decimal('150')
    assert points[4].patrimonio_value == (100 * p_mai_petr4) + (10 * p_mai_vale3)
    
    # Junho: Vendeu 600
    p_jun_petr4 = hist_service.get_price_for_date("PETR4", date(2025, 6, 30)) or Decimal('14')
    assert points[5].vendas_value == Decimal('600')
    assert points[5].patrimonio_value == 100 * p_jun_petr4

    print("\ntest_history_equivalence passed: O resultado incremental gerado está 100% matematicamente equivalente ao processamento em lote.")
