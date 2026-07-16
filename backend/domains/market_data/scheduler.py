import os
import time
import logging
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from backend.shared.db import engine
from backend.domains.market_data.service import MarketDataService
from backend.domains.market_data.macro_service import MacroIndicatorsService

logger = logging.getLogger(__name__)

class MarketDataScheduler:
    def __init__(self, service: MarketDataService, macro_service: MacroIndicatorsService = None):
        self.service = service
        self.macro_service = macro_service
        self.enabled = os.getenv("MARKET_DATA_ENABLED", "true").lower() == "true"
        self.interval_minutes = int(os.getenv("MARKET_DATA_INTERVAL", "60"))
        self.startup_sync = os.getenv("MARKET_DATA_STARTUP_SYNC", "true").lower() == "true"
        
        self._scheduler = BackgroundScheduler()

    def start(self):
        if not self.enabled:
            logger.info("MarketDataScheduler is DISABLED via .env")
            return

        logger.info(f"Starting MarketDataScheduler (Interval: {self.interval_minutes}m)...")
        
        # Add the recurring job
        self._scheduler.add_job(
            self.run_sync, 
            'interval', 
            minutes=self.interval_minutes,
            id='market_data_sync'
        )
        self._scheduler.start()
        
        # Add Macro Indicators job (Daily)
        if self.macro_service:
            logger.info("Scheduling Macro Indicators sync (Daily)...")
            self._scheduler.add_job(
                self.run_macro_sync,
                'interval',
                days=1,
                id='macro_indicators_sync'
            )
            
        # Check if startup sync is required
        if self.startup_sync:
            logger.info("MARKET_DATA_STARTUP_SYNC is enabled. Enqueueing initial sync...")
            self._scheduler.add_job(self.run_sync, 'date', id='startup_market_data_sync')
            if self.macro_service:
                self._scheduler.add_job(self.run_macro_sync, 'date', id='startup_macro_sync')

    def stop(self):
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown()
            logger.info("MarketDataScheduler stopped.")
        
    def run_sync(self):
        """Executa a sincronização chamando o serviço."""
        logger.info("--- MARKET DATA SYNC STARTED ---")
        start_time = time.time()
        
        # We need a new isolated DB session for the background job
        db_session = Session(engine)
        
        try:
            result = self.service.update_market_data(db_session)
            
            # Log specific metrics requested in prompt
            tickers_fetched = result.get("tickers_fetched", 0)
            prices_saved = result.get("prices_saved", 0)
            elapsed_time = time.time() - start_time
            
            logger.info(f"Sync Results - Fetched: {tickers_fetched} | Saved: {prices_saved} | Duration: {elapsed_time:.2f}s")
            # The service caches are updated natively inside the provider/service
            
            # Commit the session since service updated prices and valuations
            db_session.commit()
            return result
            
        except Exception as e:
            # Seguranca: Nunca interromper o backend
            db_session.rollback()
            logger.error(f"Error during Market Data sync: {str(e)}", exc_info=True)
            logger.info("Fallback: Maintaining previous prices as Yahoo Finance/Network is unavailable.")
            return {"status": "error", "message": str(e)}
        finally:
            db_session.close()
            logger.info("--- MARKET DATA SYNC ENDED ---")

    def run_macro_sync(self):
        """Executa a sincronização de indicadores macroeconômicos (CDI, SELIC, IPCA)."""
        if not self.macro_service:
            return
            
        logger.info("--- MACRO INDICATORS SYNC STARTED ---")
        start_time = time.time()
        db_session = Session(engine)
        
        try:
            result = self.macro_service.update_indicators(db_session)
            db_session.commit()
            
            elapsed = time.time() - start_time
            saved = result.get("indicators_saved", 0)
            logger.info(f"Macro Sync Results - Saved: {saved} | Duration: {elapsed:.2f}s")
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error during Macro Indicators sync: {str(e)}", exc_info=True)
        finally:
            db_session.close()
            logger.info("--- MACRO INDICATORS SYNC ENDED ---")
