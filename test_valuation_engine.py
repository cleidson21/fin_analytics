from decimal import Decimal
from backend.domains.investments.engines.position_engine import PositionResult
from backend.domains.investments.engines.valuation_engine import ValuationEngine

def mk_pos(ticker, broker, qty, avg_price, inv_val):
    return PositionResult(
        ticker=ticker,
        institution=broker,
        quantity=Decimal(str(qty)),
        average_price=Decimal(str(avg_price)),
        invested_value=Decimal(str(inv_val))
    )

def run_tests():
    engine = ValuationEngine()
    
    # 1. Ativo Valorizado (Ação)
    pos_val = mk_pos("PETR4", "NU", 100, 30.00, 3000.00)
    prices = {"PETR4": Decimal('33.00')}
    res_val = engine.calculate_valuation([pos_val], prices)
    assert res_val[0].market_value == Decimal('3300.00')
    assert res_val[0].unrealized_gain == Decimal('300.00')
    assert res_val[0].unrealized_gain_percent == Decimal('10.00')

    # 2. Ativo Desvalorizado (BDR)
    pos_des = mk_pos("AAPL34", "XP", 10, 80.00, 800.00)
    prices = {"AAPL34": Decimal('70.00')}
    res_des = engine.calculate_valuation([pos_des], prices)
    assert res_des[0].market_value == Decimal('700.00')
    assert res_des[0].unrealized_gain == Decimal('-100.00')
    assert res_des[0].unrealized_gain_percent == Decimal('-12.50')

    # 3. Ativo Sem Variação (ETF)
    pos_flat = mk_pos("IVVB11", "BTG", 100, 200.00, 20000.00)
    prices = {"IVVB11": Decimal('200.00')}
    res_flat = engine.calculate_valuation([pos_flat], prices)
    assert res_flat[0].market_value == Decimal('20000.00')
    assert res_flat[0].unrealized_gain == Decimal('0.00')
    assert res_flat[0].unrealized_gain_percent == Decimal('0.00')

    # 4. Ativo Zerado
    pos_zero = mk_pos("VALE3", "NU", 0, 0, 0)
    res_zero = engine.calculate_valuation([pos_zero], {"VALE3": Decimal('60.00')})
    assert res_zero[0].quantity == Decimal('0')
    assert res_zero[0].market_value == Decimal('0')
    assert res_zero[0].unrealized_gain == Decimal('0')

    # 5. Preço Inexistente (Deve assumir Custo de Aquisição)
    pos_no_price = mk_pos("FIIB11", "XP", 50, 400.00, 20000.00)
    res_no_price = engine.calculate_valuation([pos_no_price], {}) # vazio
    assert res_no_price[0].current_price == Decimal('400.00')
    assert res_no_price[0].market_value == Decimal('20000.00')
    assert res_no_price[0].unrealized_gain == Decimal('0.00')

    # 6. Preço Zero (Empresa quebrou, ex: OIBR3)
    pos_faliu = mk_pos("OIBR3", "XP", 1000, 5.00, 5000.00)
    res_faliu = engine.calculate_valuation([pos_faliu], {"OIBR3": Decimal('0.00')})
    assert res_faliu[0].market_value == Decimal('0.00')
    assert res_faliu[0].unrealized_gain == Decimal('-5000.00')
    assert res_faliu[0].unrealized_gain_percent == Decimal('-100.00')

    # 7. Múltiplos Ativos, Múltiplas Corretoras, Tipos Variados
    positions = [pos_val, pos_des, pos_flat]
    prices = {
        "PETR4": Decimal('33.00'),
        "AAPL34": Decimal('70.00'),
        "IVVB11": Decimal('200.00')
    }
    results = engine.calculate_valuation(positions, prices)
    assert len(results) == 3
    assert results[0].ticker == "PETR4"
    assert results[1].ticker == "AAPL34"
    assert results[2].ticker == "IVVB11"

    print("✅ TODOS OS TESTES DA VALUATION ENGINE PASSARAM!")

if __name__ == "__main__":
    run_tests()
