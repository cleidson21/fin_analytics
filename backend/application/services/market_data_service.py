from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import threading

from backend.integrations.market_data.models import MarketQuote
from backend.integrations.market_data.provider_protocol import MarketDataProvider

class MarketDataService:
    """
    Serviço de enriquecimento de mercado responsável por orquestrar
    a busca de cotações com cache em memória (TTL default de 15 min).
    """
    
    def __init__(self, provider: MarketDataProvider, ttl_minutes: int = 15):
        self.provider = provider
        self.ttl = timedelta(minutes=ttl_minutes)
        # Cache em memória simples para evitar dependências extras neste lote.
        # Estrutura: { "TICKER_CLASS": {"quote": MarketQuote, "expires_at": datetime} }
        self._cache: Dict[str, dict] = {}
        self._lock = threading.Lock()

    def get_quote(self, ticker: str, asset_class: str) -> Optional[MarketQuote]:
        """
        Retorna a cotação de mercado para um ativo.
        Utiliza cache para evitar múltiplas requisições sequenciais.
        """
        if not ticker or not asset_class:
            return None
            
        cache_key = f"{ticker}_{asset_class}"
        
        # 1. Verifica Cache
        with self._lock:
            cached_item = self._cache.get(cache_key)
            if cached_item:
                if datetime.utcnow() < cached_item["expires_at"]:
                    return cached_item["quote"]
                else:
                    # Expirado
                    del self._cache[cache_key]
                    
        # 2. Busca do Provider Externo
        quote = self.provider.get_quote(ticker, asset_class)
        
        # 3. Atualiza Cache (mesmo se for None, para fazer negative caching por curto tempo)
        with self._lock:
            # Negative caching: se deu erro, tentamos de novo em 2 minutos em vez de 15 min
            expires = datetime.utcnow() + (self.ttl if quote else timedelta(minutes=2))
            self._cache[cache_key] = {
                "quote": quote,
                "expires_at": expires
            }
            
        return quote

    def get_history(self, ticker: str, asset_class: str, period: str = "1mo") -> List[Dict[str, Any]]:
        """
        Retorna o histórico de preços com cache.
        O cache para histórico será um pouco mais longo (ex: 60 minutos), 
        pois a mudança intraday não justifica re-fetch constante para um gráfico geral,
        e previne overloading na API se houver muitos assets sendo navegados.
        """
        cache_key = f"HIST_{ticker}_{asset_class}_{period}"
        
        with self._lock:
            cached_item = self._cache.get(cache_key)
            if cached_item:
                if datetime.utcnow() < cached_item["expires_at"]:
                    return cached_item["history"]
                else:
                    del self._cache[cache_key]
                    
        history = self.provider.get_history(ticker, asset_class, period)
        
        with self._lock:
            # TTL mais alto para histórico
            ttl = timedelta(minutes=60) if history else timedelta(minutes=5)
            self._cache[cache_key] = {
                "history": history,
                "expires_at": datetime.utcnow() + ttl
            }
            
        return history

    def get_indicators(self, ticker: str, asset_class: str) -> Dict[str, Any]:
        """
        Retorna indicadores financeiros com cache longo.
        """
        cache_key = f"IND_{ticker}_{asset_class}"
        
        with self._lock:
            cached_item = self._cache.get(cache_key)
            if cached_item:
                if datetime.utcnow() < cached_item["expires_at"]:
                    return cached_item["indicators"]
                else:
                    del self._cache[cache_key]
                    
        indicators = self.provider.get_indicators(ticker, asset_class)
        
        with self._lock:
            ttl = timedelta(hours=24) if indicators else timedelta(minutes=5)
            self._cache[cache_key] = {
                "indicators": indicators,
                "expires_at": datetime.utcnow() + ttl
            }
            
        return indicators

# Instância global para ser utilizada como Singleton (cache compartilhado) nos roteadores
from backend.integrations.yfinance.yfinance_provider import YFinanceProvider
market_data_service = MarketDataService(YFinanceProvider(), ttl_minutes=15)

