import logging
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date

from backend.domains.market_data.interfaces import MarketDataProvider
from backend.domains.market_data.repository import MarketDataRepository
from backend.domains.investments.application.portfolio_application_service import PortfolioApplicationService

logger = logging.getLogger(__name__)

class MarketDataService:
    """
    Orquestra a busca de preços de mercado e repassa para a Engine atualizar os valuations.
    """
    def __init__(
        self,
        provider: MarketDataProvider,
        repository: MarketDataRepository,
        portfolio_service: PortfolioApplicationService
    ):
        self.provider = provider
        self.repository = repository
        self.portfolio_service = portfolio_service

    def _get_active_tickers(self, session: Session) -> List[str]:
        # Busca tickers que o usuário possui saldo ou posições ativas
        # O banco salva tickers na tabela assets. 
        # Idealmente, buscamos todos os assets da tabela assets.
        result = session.execute(text("SELECT ticker FROM assets")).fetchall()
        return [row[0] for row in result if row[0]]

    def update_market_data(self, session: Session) -> dict:
        """
        Rotina principal do Scheduler:
        1. Identifica os ativos
        2. Busca preços no Yahoo Finance
        3. Salva em asset_prices
        4. Aciona PortfolioApplicationService para recalcular valuations e wealth (salvando em asset_valuations).
        """
        logger.info("Starting Market Data update process...")
        tickers = self._get_active_tickers(session)
        if not tickers:
            logger.info("No active tickers found to update.")
            return {"status": "ok", "message": "No tickers found", "updated": 0}
            
        logger.info(f"Fetching prices for {len(tickers)} tickers via {self.provider.get_name()}...")
        quotes = self.provider.fetch_current_prices(tickers)
        
        # 3. Salvar em asset_prices
        saved_count = self.repository.save_prices(session, quotes)
        logger.info(f"Saved {saved_count} new price records to asset_prices.")
        
        # 4. Atualizar Valuation e Wealth
        # Para isso precisamos buscar trades, snapshots e construir market_prices.
        # No V3, a engine recalcula o Valuation baseando-se no dicionário de preços.
        market_prices = {quote.ticker: quote.close_price for quote in quotes}
        
        from backend.domains.investments.repositories.trade_repository import TradeRepository
        from backend.domains.investments.repositories.snapshot_repository import SnapshotRepository
        
        # We need the trades and snapshots to compute current positions
        trade_repo = TradeRepository()
        snapshot_repo = SnapshotRepository()
        
        user_id_result = session.execute(text("SELECT id FROM users LIMIT 1")).fetchone()
        user_id = user_id_result[0] if user_id_result else "00000000-0000-0000-0000-000000000000"
        
        trades = trade_repo.get_all(session, user_id)
        snapshots = snapshot_repo.get_latest_snapshots(session, user_id)
        
        logger.info("Recalculating Portfolio Valuations...")
        self.portfolio_service.get_current_portfolio(
            trades=trades,
            snapshots=snapshots,
            market_prices=market_prices,
            session=session
        )
        
        return {
            "status": "success",
            "provider": self.provider.get_name(),
            "tickers_fetched": len(quotes),
            "prices_saved": saved_count,
            "valuations_updated": True
        }
