import logging
import uuid
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date
from decimal import Decimal
from pydantic import BaseModel

from backend.domains.investments.repositories.broker_alias_resolver import BrokerAliasResolver

logger = logging.getLogger(__name__)

class DividendDTO(BaseModel):
    ticker: str
    broker: str
    dividend_type: str
    currency: str = "BRL"
    ex_date: date
    payment_date: date
    quantity_held: Decimal
    value_per_share: Decimal
    gross_amount: Decimal
    irrf_tax: Decimal = Decimal('0')
    source: str = "BROKER_NOTE"

class DividendRepository:
    """
    Repositório para persistir os pagamentos de proventos na tabela dividends do V3.
    """
    def __init__(self, broker_resolver: Optional[BrokerAliasResolver] = None):
        self._asset_cache: Dict[str, str] = {}
        self._account_cache: Dict[str, str] = {}
        self._broker_resolver = broker_resolver or BrokerAliasResolver()
        
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

    def save_dividends(self, session: Session, dividends: List[DividendDTO]) -> None:
        if not dividends:
            return
            
        query = text("""
            INSERT INTO dividends (
                id, asset_id, account_id, type, currency, ex_date, payment_date, 
                quantity_held, value_per_share, gross_amount, irrf_tax, source
            ) VALUES (
                :id, :asset_id, :account_id, :type, :currency, :ex_date, :payment_date, 
                :quantity_held, :value_per_share, :gross_amount, :irrf_tax, :source
            ) ON CONFLICT(asset_id, account_id, ex_date, type) DO UPDATE SET
                currency=excluded.currency,
                payment_date=excluded.payment_date,
                quantity_held=excluded.quantity_held,
                value_per_share=excluded.value_per_share,
                gross_amount=excluded.gross_amount,
                irrf_tax=excluded.irrf_tax,
                source=excluded.source
        """)
        
        for div in dividends:
            try:
                asset_id = self._resolve_asset_id(session, div.ticker)
                account_id = self._resolve_account_id(session, div.broker)
                
                params = {
                    "id": str(uuid.uuid4()),
                    "asset_id": asset_id,
                    "account_id": account_id,
                    "type": div.dividend_type,
                    "currency": div.currency,
                    "ex_date": div.ex_date.isoformat(),
                    "payment_date": div.payment_date.isoformat(),
                    "quantity_held": float(div.quantity_held),
                    "value_per_share": int(round(float(div.value_per_share) * 100)),
                    "gross_amount": int(round(float(div.gross_amount) * 100)),
                    "irrf_tax": int(round(float(div.irrf_tax) * 100)),
                    "source": div.source
                }
                session.execute(query, params)
            except Exception as e:
                logger.warning(f"Could not save dividend for {div.ticker}: {e}")
                
        session.commit()
