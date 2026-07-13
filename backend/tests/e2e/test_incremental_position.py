import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from datetime import date
from decimal import Decimal
from backend.domains.investments.dto import TradeDTO, TradeType
from backend.domains.investments.engines.position_engine import PositionEngine

def test_incremental_position_restore():
    """
    Testa se o PositionEngine restaura perfeitamente o estado quando
    recebe uma operação INITIAL_POSITION sintética.
    Isso valida a premissa base do algoritmo O(N+M) do HistoryService.
    """
    engine = PositionEngine()
    
    # 1. Estado original calculado do zero
    trades_m1 = [
        TradeDTO(ticker="ITUB4", broker="XP", operation_type=TradeType.BUY, trade_date=date(2025, 1, 10), quantity=Decimal('100'), unit_price=Decimal('25'), total_value=Decimal('2500'), source="T", idempotency_hash="1"),
        TradeDTO(ticker="ITUB4", broker="XP", operation_type=TradeType.BUY, trade_date=date(2025, 1, 15), quantity=Decimal('100'), unit_price=Decimal('27'), total_value=Decimal('2700'), source="T", idempotency_hash="2"),
        TradeDTO(ticker="ITUB4", broker="XP", operation_type=TradeType.SELL, trade_date=date(2025, 1, 20), quantity=Decimal('50'), unit_price=Decimal('30'), total_value=Decimal('1500'), source="T", idempotency_hash="3"),
    ]
    
    pos_m1 = engine.calculate_position(trades_m1, [])
    assert len(pos_m1) == 1
    p1 = pos_m1[0]
    
    # Validação do estado no fim do mês 1
    assert p1.quantity == Decimal('150')
    assert p1.average_price == Decimal('26') # (2500+2700)/200
    assert p1.invested_value == Decimal('3900') # 150 * 26
    
    # 2. Restaurar estado no mês 2 via INITIAL_POSITION + novos trades
    trades_m2 = [
        TradeDTO(
            ticker=p1.ticker,
            broker=p1.institution,
            operation_type=TradeType.INITIAL_POSITION,
            trade_date=date(2025, 2, 1),
            quantity=p1.quantity,
            unit_price=p1.average_price,
            total_value=p1.invested_value,
            source="HIST",
            idempotency_hash="init"
        ),
        TradeDTO(ticker="ITUB4", broker="XP", operation_type=TradeType.BUY, trade_date=date(2025, 2, 10), quantity=Decimal('50'), unit_price=Decimal('22'), total_value=Decimal('1100'), source="T", idempotency_hash="4"),
    ]
    
    pos_m2 = engine.calculate_position(trades_m2, [])
    assert len(pos_m2) == 1
    p2 = pos_m2[0]
    
    # Validação do estado no fim do mês 2
    assert p2.quantity == Decimal('200') # 150 + 50
    assert p2.invested_value == Decimal('5000') # 3900 + 1100
    assert p2.average_price == Decimal('25') # 5000 / 200
    
    # 3. Comparar com o cálculo batch (processando do zero)
    pos_batch = engine.calculate_position(trades_m1 + [trades_m2[1]], [])
    p_batch = pos_batch[0]
    
    assert p2.quantity == p_batch.quantity
    assert p2.average_price == p_batch.average_price
    assert p2.invested_value == p_batch.invested_value
    
    print("\ntest_incremental_position_restore passed: O estado restaurado via INITIAL_POSITION é idêntico ao cálculo batch completo.")
