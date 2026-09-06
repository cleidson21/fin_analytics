import yfinance as yf
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
import logging

from backend.integrations.market_data.models import MarketQuote
from backend.integrations.market_data.provider_protocol import MarketDataProvider

logger = logging.getLogger(__name__)

class YFinanceProvider(MarketDataProvider):
    """
    Implementação do provedor de Market Data utilizando a biblioteca yfinance.
    """
    
    def __init__(self):
        self._usd_brl_rate: Optional[float] = None
        self._usd_brl_expires_at: Optional[datetime] = None

    def _get_usd_to_brl_rate(self) -> float:
        """Busca a taxa de câmbio USD/BRL e faz cache em memória por 1 hora."""
        now = datetime.utcnow()
        if self._usd_brl_rate and self._usd_brl_expires_at and now < self._usd_brl_expires_at:
            return self._usd_brl_rate
            
        try:
            ticker = yf.Ticker("BRL=X")
            hist = ticker.history(period="1d")
            if not hist.empty:
                self._usd_brl_rate = float(hist.iloc[-1]['Close'])
                from datetime import timedelta
                self._usd_brl_expires_at = now + timedelta(hours=1)
                return self._usd_brl_rate
        except Exception as e:
            logger.warning(f"Erro ao buscar taxa USD/BRL: {e}")
            
        # Fallback rate if yfinance fails
        return self._usd_brl_rate or 5.0
    
    def _normalize_ticker(self, ticker: str, asset_class: str) -> Optional[str]:
        """
        Gera o símbolo reconhecido pelo Yahoo Finance com base no ativo governado.
        Retorna None se a classe não for suportada ou o ticker for duvidoso.
        """
        ticker = ticker.strip().upper()
        
        if asset_class == "CRYPTO":
            return f"{ticker}-USD"
            
        elif asset_class == "ETF_GLOBAL":
            # Geralmente listados no mercado americano (ex: IVV, AGG, VXUS)
            return ticker
            
        elif asset_class in ["STOCK", "FII"]:
            # Ativos B3
            return f"{ticker}.SA"
            
        elif asset_class == "BDR":
            # Se possui números (ex: BABA34), é um BDR real da B3.
            if any(char.isdigit() for char in ticker):
                return f"{ticker}.SA"
            # Se não possui números (ex: BABA), é o ativo original americano (Avenue etc).
            return ticker
            
        # FIXED_INCOME, OTHER, ou classes desconhecidas
        return None

    def get_quote(self, ticker: str, asset_class: str) -> Optional[MarketQuote]:
        yf_symbol = self._normalize_ticker(ticker, asset_class)
        if not yf_symbol:
            return None
            
        try:
            # Não faz download em massa. Pega apenas o histórico de 1 dia ou 5 dias para garantir que há preço recente.
            # Utilizamos period="5d" para cobrir finais de semana e feriados
            yf_ticker = yf.Ticker(yf_symbol)
            hist = yf_ticker.history(period="5d")
            
            if hist.empty:
                logger.warning(f"YFinance sem dados para {yf_symbol}")
                return None
                
            # Pega o último fechamento (Close)
            last_row = hist.iloc[-1]
            price_float = float(last_row['Close'])
            
            # Verifica se precisa converter USD -> BRL
            is_usd = asset_class in ["ETF_GLOBAL", "CRYPTO"] or (asset_class == "BDR" and not any(char.isdigit() for char in ticker))
            
            if is_usd:
                rate = self._get_usd_to_brl_rate()
                price_float = price_float * rate
                
            price = Decimal(str(round(price_float, 2)))
            # O índice do pandas DataFrame retornado pelo yfinance é um datetime com timezone
            date_obj = hist.index[-1].to_pydatetime()
            
            return MarketQuote(
                provider="YFINANCE",
                source_ticker=yf_symbol,
                price=price,
                price_date=date_obj,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.warning(f"Erro ao buscar MarketQuote para {ticker} via yfinance: {e}")
            return None

    def get_history(self, ticker: str, asset_class: str, period: str = "1mo") -> List[Dict[str, Any]]:
        norm_ticker = self._normalize_ticker(ticker, asset_class)
        if not norm_ticker:
            logger.debug(f"Ticker {ticker} (Classe: {asset_class}) não suportado pelo YFinanceProvider para histórico.")
            return []
            
        try:
            yt = yf.Ticker(norm_ticker)
            # Retorna df com datetime index
            hist = yt.history(period=period)
            
            if hist.empty:
                logger.debug(f"Histórico retornado vazio pelo YFinance para {norm_ticker} (period={period}).")
                return []
                
            history_data = []
            
            # Verifica se precisa converter USD -> BRL
            is_usd = asset_class in ["ETF_GLOBAL", "CRYPTO"] or (asset_class == "BDR" and not any(char.isdigit() for char in ticker))
            rate = self._get_usd_to_brl_rate() if is_usd else 1.0
            
            for date_idx, row in hist.iterrows():
                history_data.append({
                    "date": date_idx.strftime("%Y-%m-%d"),
                    "close": float(row["Close"]) * rate,
                    "open": float(row["Open"]) * rate,
                    "high": float(row["High"]) * rate,
                    "low": float(row["Low"]) * rate,
                    "volume": int(row["Volume"])
                })
                
            return history_data
            
        except Exception as e:
            logger.warning(f"Erro ao buscar histórico para {ticker} via yfinance: {e}")
            return []

    def get_indicators(self, ticker: str, asset_class: str) -> Dict[str, Any]:
        norm_ticker = self._normalize_ticker(ticker, asset_class)
        if not norm_ticker:
            return {}
            
        try:
            yt = yf.Ticker(norm_ticker)
            info = yt.info
            
            # Extract relevant indicators
            indicators = {}
            if "trailingPE" in info:
                indicators["P/L"] = f"{info['trailingPE']:.2f}"
            if "priceToBook" in info:
                indicators["P/VP"] = f"{info['priceToBook']:.2f}"
            if "dividendYield" in info and info["dividendYield"] is not None:
                indicators["Div. Yield"] = f"{info['dividendYield']:.2f}%"
            if "beta" in info:
                indicators["Beta"] = f"{info['beta']:.2f}"
            if "marketCap" in info:
                # Format market cap
                mc = info["marketCap"]
                if mc >= 1e9:
                    indicators["Valor de Mercado"] = f"R$ {mc / 1e9:.2f}B"
                elif mc >= 1e6:
                    indicators["Valor de Mercado"] = f"R$ {mc / 1e6:.2f}M"
                else:
                    indicators["Valor de Mercado"] = f"R$ {mc}"
                    
            return indicators
            
        except Exception as e:
            logger.warning(f"Erro ao buscar indicadores para {ticker} via yfinance: {e}")
            return {}
