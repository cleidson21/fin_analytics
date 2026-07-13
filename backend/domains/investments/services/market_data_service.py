from datetime import date
from decimal import Decimal
from backend.domains.investments.repositories.market_data_repository import MarketDataRepository
from backend.domains.investments.dto import MarketDataPoint

class MarketDataService:
    """
    Serviço de fornecimento de séries históricas de benchmarks.
    Isola a PerformanceEngine do acesso direto aos dados ou CSV.
    """
    
    def __init__(self):
        self.repo = MarketDataRepository()

    def get_market_data(self, target_date: date) -> MarketDataPoint:
        """
        Retorna o ponto de dados de mercado (todos os benchmarks) para uma data específica.
        """
        return MarketDataPoint(
            date=target_date,
            ibov=self.repo.get_by_date("ibov", target_date),
            cdi=self.repo.get_by_date("cdi", target_date),
            ifix=self.repo.get_by_date("ifix", target_date),
            ipca=self.repo.get_by_date("ipca", target_date),
            sp500=self.repo.get_by_date("sp500", target_date),
            idiv=self.repo.get_by_date("idiv", target_date)
        )
