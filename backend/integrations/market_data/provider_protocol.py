from typing import Protocol, Optional, List, Dict, Any
from .models import MarketQuote

class MarketDataProvider(Protocol):
    """
    Protocolo base para providers de Market Data.
    """
    
    def get_quote(self, ticker: str, asset_class: str) -> Optional[MarketQuote]:
        """
        Retorna a cotação de mercado para um ticker.
        
        Args:
            ticker: Ticker interno governado (ex: KNCR11)
            asset_class: Classe do ativo (ex: FII, STOCK)
            
        Returns:
            MarketQuote se houver cotação válida, None caso contrário.
        """
        ...

    def get_history(self, ticker: str, asset_class: str, period: str = "1mo") -> List[Dict[str, Any]]:
        """
        Retorna uma série histórica de preços.
        O formato esperado é uma lista de dicionários contendo ao menos {"date": "YYYY-MM-DD", "close": float}.
        """
        ...
        
    def get_indicators(self, ticker: str, asset_class: str) -> Dict[str, Any]:
        """
        Retorna indicadores financeiros.
        """
        ...
