from backend.domains.investments.application_factory import ApplicationFactory
import sys
import os
from datetime import date
from decimal import Decimal
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from backend.domains.investments.services.history_service import HistoryService
from backend.domains.investments.repositories.historical_price_repository import HistoricalPriceRepository
from backend.domains.investments.dto import TradeDTO, TradeType

def test_historical_portfolio():
    """
    Testa se o pipeline integrado do HistoryService processa meses históricos
    solicitando preços dinâmicos que progridem mensalmente.
    """
    HistoricalPriceRepository(data_dir="database/prices")
    
    trades = [
        TradeDTO(ticker="PETR4", broker="XP", operation_type=TradeType.BUY, trade_date=date(2020, 1, 10), quantity=Decimal('100'), unit_price=Decimal('25'), total_value=Decimal('2500'), source="T", idempotency_hash="1"),
    ]
    
    market_prices = {"PETR4": Decimal('50')}
    
    service = ApplicationFactory.get_history_service()
    history = service.generate_history(
        trades=trades,
        snapshots=[],
        market_prices=market_prices,
        start_date=date(2020, 1, 1),
        end_date=date(2020, 4, 30),
        granularity="month"
    )
    
    points = history.points
    assert len(points) == 4
    
    # 2020-01: o preço mockado era ~30.00
    # 2020-02: o preço foi crescendo a 0.05% por dia (~30.46)
    
    p_jan = points[0].patrimonio_value
    p_fev = points[1].patrimonio_value
    p_mar = points[2].patrimonio_value
    p_abr = points[3].patrimonio_value
    
    # No antigo comportamento O(N*M), todos os meses teriam patrimônio_value == 5000 (preço atual '50' x 100).
    # Com a refatoração, o patrimônio deve acompanhar o preço simulado flutuando no tempo, sendo menor no começo.
    assert Decimal('3000') <= p_jan <= Decimal('3100')
    assert p_jan < p_fev < p_mar < p_abr
    assert p_abr < Decimal('5000') # ainda não atingiu o preço atual de 50
    
    print("\ntest_historical_portfolio passed: Pipeline histórico de patrimônio dinâmico implementado com sucesso sem destruir retrocompatibilidade.")
