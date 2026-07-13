from decimal import Decimal
from backend.domains.investments.engines.valuation_engine import ValuationResult
from backend.domains.investments.engines.wealth_engine import WealthEngine

def mk_val(ticker, inst, qty, cb, mv):
    # Dummy result based on input
    return ValuationResult(
        ticker=ticker,
        institution=inst,
        quantity=Decimal(str(qty)),
        cost_basis=Decimal(str(cb)),
        average_cost=Decimal('0'), # unused by wealth engine
        current_price=Decimal('0'), # unused by wealth engine
        market_value=Decimal(str(mv)),
        unrealized_gain=Decimal(str(mv)) - Decimal(str(cb)),
        unrealized_gain_percent=Decimal('0') # Recalculated by wealth engine
    )

def run_tests():
    engine = WealthEngine()
    
    # 1. Carteira vazia
    res_vazia = engine.calculate([])
    assert res_vazia.total_market_value == Decimal('0')
    assert res_vazia.asset_count == 0
    assert res_vazia.institution_count == 0
    
    # 2. Único ativo
    v1 = mk_val("PETR4", "NU", 100, 3000, 3300)
    res_unico = engine.calculate([v1], {"PETR4": "STOCK"})
    assert res_unico.total_market_value == Decimal('3300')
    assert res_unico.total_unrealized_gain == Decimal('300')
    assert res_unico.total_unrealized_gain_percent == Decimal('10')
    assert res_unico.asset_count == 1
    assert res_unico.by_class[0].allocation_percent == Decimal('100')

    # 3. Múltiplos ativos, múltiplas instituições, múltiplas classes
    # v1 (NU, PETR4) -> 3300
    v2 = mk_val("VALE3", "XP", 200, 10000, 12000)
    v3 = mk_val("IVVB11", "XP", 50, 5000, 4700) # Perda de 300
    v4 = mk_val("PETR4", "BTG", 100, 3000, 3300) # Mesmo ativo, outra corretora
    
    class_map = {"PETR4": "STOCK", "VALE3": "STOCK", "IVVB11": "ETF"}
    
    res_multi = engine.calculate([v1, v2, v3, v4], class_map)
    # Total Market Value = 3300 + 12000 + 4700 + 3300 = 23300
    # Total Cost = 3000 + 10000 + 5000 + 3000 = 21000
    assert res_multi.total_market_value == Decimal('23300')
    assert res_multi.total_cost_basis == Decimal('21000')
    assert res_multi.asset_count == 3 # PETR4, VALE3, IVVB11
    assert res_multi.institution_count == 3 # NU, XP, BTG
    
    # Verificação de aglutinação de ativo (PETR4)
    petr4_sum = next(a for a in res_multi.by_asset if a.ticker == "PETR4")
    assert petr4_sum.market_value == Decimal('6600')
    assert petr4_sum.cost_basis == Decimal('6000')
    # Allocation: 6600 / 23300 ~ 28.32%
    
    # Verificação de instituição (XP)
    xp_sum = next(i for i in res_multi.by_institution if i.institution == "XP")
    assert xp_sum.market_value == Decimal('16700') # 12000 (VALE3) + 4700 (IVVB11)
    
    # Verificação de classe (STOCK)
    stock_sum = next(c for c in res_multi.by_class if c.asset_class == "STOCK")
    assert stock_sum.market_value == Decimal('18600') # 6600 (PETR4) + 12000 (VALE3)
    
    # 4. Patrimônio igual ao custo
    v_flat = mk_val("WEGE3", "XP", 10, 1000, 1000)
    res_flat = engine.calculate([v_flat])
    assert res_flat.total_unrealized_gain == Decimal('0')
    assert res_flat.total_unrealized_gain_percent == Decimal('0')

    # 5. Ativo sem preço (Cost Basis = Market Value vindo da ValuationEngine)
    v_noprice = mk_val("OIBR3", "NU", 1000, 500, 500)
    res_noprice = engine.calculate([v_noprice])
    assert res_noprice.total_unrealized_gain == Decimal('0')
    
    # 6. Ativo zerado
    v_zero = mk_val("MGLU3", "NU", 0, 0, 0)
    res_zero = engine.calculate([v_zero, v_flat])
    assert res_zero.asset_count == 1 # Ignora o zerado
    assert res_zero.total_market_value == Decimal('1000')
    
    # 7. Divisão por zero (Custo zero, Market Value positivo) -> ex: bônus
    v_bonus = mk_val("BNS", "XP", 10, 0, 100)
    res_bonus = engine.calculate([v_bonus])
    assert res_bonus.total_unrealized_gain_percent == Decimal('100')
    
    # 8. Cálculo de participação decrescente (Sort test)
    # res_multi: XP(16700), BTG(3300), NU(3300)
    assert res_multi.by_institution[0].institution == "XP"
    # Allocation soma 100%
    alloc_sum = sum(i.allocation_percent for i in res_multi.by_institution)
    # Tem que ser exatamente 100 (podem haver dizimas periódicas se a precisão estourar, mas 
    # Decimal mantém exatidão até sua config de context. Geralmente, somam 100.000...)
    # Vamos validar que round(alloc_sum) == 100
    assert alloc_sum.to_integral_value() == Decimal('100')

    print("✅ TODOS OS TESTES DA WEALTH ENGINE PASSARAM!")

if __name__ == "__main__":
    run_tests()
