import bisect
from datetime import date
from typing import Optional
from decimal import Decimal
from backend.domains.investments.repositories.historical_price_repository import HistoricalPriceRepository

class HistoricalPriceService:
    """
    Serviço que provê preços históricos de mercado de ativos.
    Pesquisa O(log N) em cache de memória e possui fallback para pregões passados.
    """
    def __init__(self, historical_price_repo: HistoricalPriceRepository):
        self.repo = historical_price_repo

    def get_price_for_date(self, ticker: str, target_date: date) -> Optional[Decimal]:
        """
        Busca o preço de fechamento para a data exata.
        Se não houver pregão na data exata, realiza fallback (O(1) pós busca binária)
        para o último dia útil disponível anterior à data.
        Nunca retorna preços do futuro.
        """
        series = self.repo.get_price_series(ticker)
        if not series:
            return None
            
        # Extrai apenas as datas para o bisect
        # (Em python, bisect suporta tuplas ordenadas diretamente, podemos usar um dummy)
        # O index_right nos diz onde inserir (target_date, infinito).
        # Logo, index_right - 1 é o maior elemento <= target_date.
        
        idx = bisect.bisect_right(series, (target_date, Decimal('Infinity')))
        
        if idx == 0:
            # target_date é mais antigo que nosso primeiro registro histórico
            return None
            
        # O último pregão válido <= target_date
        match_date, price = series[idx - 1]
        
        return price
