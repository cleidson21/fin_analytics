import sys
from decimal import Decimal
from datetime import date
from backend.domains.investments.adapters.open_finance_adapter import OpenFinanceAdapter
from backend.domains.investments.dto import AssetTypeEnum, TradeType

def run_tests():
    adapter = OpenFinanceAdapter()
    
    # 1. Payload válido de posição
    valid_pos = [{
        "reference_date": "2024-01-01",
        "ticker": "PETR4",
        "institution": "NUBANK",
        "quantity": 100.5,
        "unit_price": 30.50,
        "total_value": 3065.25,
        "asset_type": "STOCK",
        "metadata": {"source_id": "123"}
    }]
    snaps = adapter.parse_positions(valid_pos)
    assert len(snaps) == 1
    assert snaps[0].ticker == "PETR4"
    assert snaps[0].quantity == Decimal("100.5")
    assert snaps[0].unit_price == Decimal("30.50")
    assert snaps[0].asset_type == AssetTypeEnum.STOCK
    assert snaps[0].snapshot_hash is not None
    
    # 2. Payload válido de trade
    valid_trade = [{
        "trade_date": "2024-01-02",
        "ticker": "VALE3",
        "broker": "XP INVESTIMENTOS",
        "operation_type": "BUY",
        "quantity": 50,
        "unit_price": "60.00",
        "total_value": 3000.00
    }]
    trades = adapter.parse_trades(valid_trade)
    assert len(trades) == 1
    assert trades[0].operation_type == TradeType.BUY
    assert trades[0].total_value == Decimal("3000.00")
    assert trades[0].idempotency_hash is not None

    # 3. Payload vazio
    assert adapter.parse_positions([]) == []
    assert adapter.parse_trades([]) == []

    # 4. Campos obrigatórios ausentes
    try:
        adapter.parse_positions([{"ticker": "PETR4"}])
        assert False, "Should fail on missing fields"
    except ValueError as e:
        assert "Missing required key" in str(e)

    # 5. Tipos inválidos (metadata = list instead of dict)
    try:
        adapter.parse_positions([{
            "reference_date": "2024-01-01",
            "ticker": "PETR4",
            "institution": "NUBANK",
            "quantity": 100,
            "metadata": []
        }])
        assert False, "Should fail on invalid metadata type"
    except ValueError as e:
        assert "Metadata must be a dictionary" in str(e)

    # 6. Datas inválidas
    try:
        adapter.parse_trades([{
            "trade_date": "01-01-2024", # wrong format
            "ticker": "VALE3",
            "broker": "XP INVESTIMENTOS",
            "operation_type": "BUY",
            "quantity": 50,
            "unit_price": 60,
            "total_value": 3000
        }])
        assert False, "Should fail on bad date"
    except ValueError as e:
        assert "Invalid date format" in str(e)

    # 7. Ticker inválido
    try:
        adapter.parse_positions([{
            "reference_date": "2024-01-01",
            "ticker": "",
            "institution": "NUBANK",
            "quantity": 100
        }])
        assert False, "Should fail on empty ticker"
    except ValueError as e:
        assert "Invalid ticker" in str(e) or "Ticker cannot be empty" in str(e)

    # 8. Instituição inválida
    try:
        adapter.parse_trades([{
            "trade_date": "2024-01-02",
            "ticker": "VALE3",
            "broker": None,
            "operation_type": "BUY",
            "quantity": 50,
            "unit_price": 60,
            "total_value": 3000
        }])
        assert False, "Should fail on null broker"
    except ValueError as e:
        assert "Invalid institution" in str(e)

    # 9 & 10. Múltiplos ativos e múltiplas corretoras + Payload parcialmente válido
    multi_payload = [
        valid_pos[0],
        {
            "reference_date": "2024-01-01",
            "ticker": "ITUB4",
            "institution": "BTG PACTUAL",
            "quantity": 200,
            "unit_price": 30.50,
            "total_value": 6100.00
        },
        {"invalid": "item"}
    ]
    try:
        adapter.parse_positions(multi_payload)
        assert False, "Should fail completely due to the invalid item (atomic validation)"
    except ValueError as e:
        assert "Missing required key" in str(e)
        
    # Just the valid ones
    snaps_multi = adapter.parse_positions(multi_payload[:2])
    assert len(snaps_multi) == 2
    assert snaps_multi[0].institution == "NUBANK"
    assert snaps_multi[1].institution == "BTG PACTUAL"

    print("✅ TODOS OS TESTES DO ADAPTER PASSARAM!")

if __name__ == "__main__":
    run_tests()
