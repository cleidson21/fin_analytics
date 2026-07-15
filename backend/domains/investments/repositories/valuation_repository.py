import logging
import uuid
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.domains.investments.engines.valuation_engine import ValuationResult
from backend.domains.investments.repositories.broker_alias_resolver import BrokerAliasResolver
from decimal import Decimal
from datetime import date

logger = logging.getLogger(__name__)

class ValuationRepository:
    """
    Repositório para salvar a posição marcada a mercado (MTM) na tabela asset_valuations.
    """
    def __init__(self, broker_resolver: Optional[BrokerAliasResolver] = None):
        self._asset_cache: Dict[str, str] = {}
        self._account_cache: Dict[str, str] = {}
        self._broker_resolver = broker_resolver or BrokerAliasResolver()
        self._default_user_id: Optional[str] = None
        
    def _get_default_user_id(self, session: Session) -> str:
        if self._default_user_id:
            return self._default_user_id
        result = session.execute(text("SELECT id FROM users LIMIT 1")).fetchone()
        if not result:
            # Fallback seguro caso não haja user (Single User approach do V3)
            # Na fase 2.1 um usuário foi criado no seed
            return "00000000-0000-0000-0000-000000000000"
        self._default_user_id = result[0]
        return self._default_user_id

    def _resolve_asset_id(self, session: Session, ticker: str) -> str:
        if ticker in self._asset_cache:
            return self._asset_cache[ticker]
        result = session.execute(text("SELECT id FROM assets WHERE ticker = :ticker"), {"ticker": ticker}).fetchone()
        if not result:
            raise ValueError(f"Asset not found for ticker: {ticker}")
        self._asset_cache[ticker] = result[0]
        return result[0]
        
    def _resolve_account_id(self, session: Session, broker: str) -> str:
        canonical = self._broker_resolver.resolve(broker)
        if canonical in self._account_cache:
            return self._account_cache[canonical]
        result = session.execute(text("SELECT id FROM accounts WHERE name LIKE :broker LIMIT 1"), {"broker": f"%{canonical}%"}).fetchone()
        if not result:
            raise ValueError(f"Account (Broker) not found: {broker}")
        self._account_cache[canonical] = result[0]
        return result[0]

    def save_valuations(self, session: Session, valuations: List[ValuationResult], price_date: date) -> None:
        if not valuations:
            return
            
        user_id = self._get_default_user_id(session)
        
        query = text("""
            INSERT INTO asset_valuations (
                id, user_id, account_id, asset_id, last_price, market_value, 
                unrealized_gain, unrealized_gain_pct, portfolio_weight, price_date
            ) VALUES (
                :id, :user_id, :account_id, :asset_id, :last_price, :market_value, 
                :unrealized_gain, :unrealized_gain_pct, :portfolio_weight, :price_date
            ) ON CONFLICT(user_id, account_id, asset_id) DO UPDATE SET
                last_price=excluded.last_price,
                market_value=excluded.market_value,
                unrealized_gain=excluded.unrealized_gain,
                unrealized_gain_pct=excluded.unrealized_gain_pct,
                portfolio_weight=excluded.portfolio_weight,
                price_date=excluded.price_date,
                computed_at=strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
        """)
        
        total_market_value = sum(v.market_value for v in valuations)
        
        for val in valuations:
            if val.quantity <= 0:
                continue
                
            try:
                asset_id = self._resolve_asset_id(session, val.ticker)
                account_id = self._resolve_account_id(session, val.institution)
                
                weight = 0.0
                if total_market_value > 0:
                    weight = float(val.market_value / total_market_value)
                
                params = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "account_id": account_id,
                    "asset_id": asset_id,
                    "last_price": int(round(float(val.current_price) * 100)),
                    "market_value": int(round(float(val.market_value) * 100)),
                    "unrealized_gain": int(round(float(val.unrealized_gain) * 100)),
                    "unrealized_gain_pct": float(val.unrealized_gain_percent) / 100.0,
                    "portfolio_weight": weight,
                    "price_date": price_date.isoformat()
                }
                session.execute(query, params)
            except Exception as e:
                logger.warning(f"Could not save valuation for {val.ticker}: {e}")
                
        session.commit()
