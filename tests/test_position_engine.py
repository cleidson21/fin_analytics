from decimal import Decimal
from datetime import date, datetime
from backend.domains.investments.dto import TradeDTO, PositionSnapshot, AssetTypeEnum, TradeType
from backend.domains.investments.engines.position_engine import PositionEngine, PositionResult

def mk_trade(ticker, broker, t_type, qty, price, t_date):
    return TradeDTO(
        ticker=ticker,
        broker=broker,
        operation_type=t_type,
        trade_date=date.fromisoformat(t_date),
        quantity=Decimal(str(qty)),
        unit_price=Decimal(str(price)),
        total_value=Decimal(str(qty)) * Decimal(str(price)),
        source="TEST",
        idempotency_hash="hash",
        created_at=datetime.utcnow()
    )

def mk_snap(ticker, broker, qty, r_date):
    return PositionSnapshot(
        source_system="TEST",
        reference_date=date.fromisoformat(r_date),
        ticker=ticker,
        asset_type=AssetTypeEnum.STOCK,
        institution=broker,
        quantity=Decimal(str(qty)),
        snapshot_hash="hash"
    )

def run_tests():
    engine = PositionEngine()
    
    # 1. Compra única, ativo sem snapshot, ativo inexistente no snapshot
    t1 = mk_trade("PETR4", "NUBANK", TradeType.BUY, 100, 30.00, "2024-01-01")
    res1 = engine.calculate_position([t1], [])
    assert len(res1) == 1
    assert res1[0].quantity == Decimal('100')
    assert res1[0].average_price == Decimal('30.00')
    assert res1[0].invested_value == Decimal('3000.00')
    assert res1[0].snapshot_quantity is None
    assert res1[0].divergence_quantity == Decimal('0')
    
    # 2. Múltiplas compras (Custo médio)
    t2 = mk_trade("PETR4", "NUBANK", TradeType.BUY, 100, 40.00, "2024-01-02")
    res2 = engine.calculate_position([t1, t2], [])
    assert res2[0].quantity == Decimal('200')
    assert res2[0].average_price == Decimal('35.00') # (3000+4000)/200
    assert res2[0].invested_value == Decimal('7000.00')
    
    # 3. Venda parcial
    t3 = mk_trade("PETR4", "NUBANK", TradeType.SELL, 50, 50.00, "2024-01-03")
    res3 = engine.calculate_position([t1, t2, t3], [])
    assert res3[0].quantity == Decimal('150')
    assert res3[0].average_price == Decimal('35.00') # Custo não muda na venda
    assert res3[0].invested_value == Decimal('5250.00') # 150 * 35

    # 4. Venda total (posição zerada)
    t4 = mk_trade("PETR4", "NUBANK", TradeType.SELL, 150, 60.00, "2024-01-04")
    res4 = engine.calculate_position([t1, t2, t3, t4], [])
    assert res4[0].quantity == Decimal('0')
    assert res4[0].average_price == Decimal('0')
    assert res4[0].invested_value == Decimal('0')

    # 5. INITIAL_POSITION & Snapshot divergente
    t_init = mk_trade("VALE3", "XP", TradeType.INITIAL_POSITION, 300, 60.00, "2023-12-01")
    s_vale = mk_snap("VALE3", "XP", 310, "2024-01-01")
    res5 = engine.calculate_position([t_init], [s_vale])
    assert res5[0].quantity == Decimal('300')
    assert res5[0].snapshot_quantity == Decimal('310')
    assert res5[0].divergence_quantity == Decimal('10') # Snapshot tem 10 a mais
    
    # 6. TRANSFER_IN, TRANSFER_OUT
    t_in = mk_trade("ITUB4", "BTG", TradeType.TRANSFER_IN, 100, 20.00, "2024-02-01")
    t_out = mk_trade("ITUB4", "BTG", TradeType.TRANSFER_OUT, 40, 25.00, "2024-02-02")
    res6 = engine.calculate_position([t_in, t_out], [])
    assert res6[0].quantity == Decimal('60')
    assert res6[0].average_price == Decimal('20.00')
    assert res6[0].invested_value == Decimal('1200.00')

    # 7. AMORTIZATION
    t_fii = mk_trade("MXRF11", "NU", TradeType.BUY, 100, 10.00, "2024-01-01") # invested 1000
    t_am = mk_trade("MXRF11", "NU", TradeType.AMORTIZATION, 100, 0.50, "2024-02-01") # return 50
    res7 = engine.calculate_position([t_fii, t_am], [])
    assert res7[0].quantity == Decimal('100')
    assert res7[0].invested_value == Decimal('950.00')
    assert res7[0].average_price == Decimal('9.50')

    # 8. Múltiplas corretoras e Múltiplos Ativos (Mix)
    all_trades = [t1, t2, t_init, t_in]
    all_snaps = [s_vale]
    res8 = engine.calculate_position(all_trades, all_snaps)
    # Tem que ter PETR4-NUBANK, VALE3-XP, ITUB4-BTG
    assert len(res8) == 3
    for r in res8:
        if r.ticker == "PETR4":
            assert r.quantity == Decimal('200')
        elif r.ticker == "VALE3":
            assert r.quantity == Decimal('300')
            assert r.divergence_quantity == Decimal('10')
        elif r.ticker == "ITUB4":
            assert r.quantity == Decimal('100')
            
    # 9. Ativo sem Trades, apenas Snapshot (ex: veio do Open Finance, mas a pessoa apagou as notas)
    s_only = mk_snap("WEGE3", "XP", 50, "2024-01-01")
    res9 = engine.calculate_position([], [s_only])
    assert len(res9) == 1
    assert res9[0].ticker == "WEGE3"
    assert res9[0].quantity == Decimal('0')
    assert res9[0].snapshot_quantity == Decimal('50')
    assert res9[0].divergence_quantity == Decimal('50')

    print("✅ TODOS OS TESTES DA POSITION ENGINE PASSARAM!")

if __name__ == "__main__":
    run_tests()
