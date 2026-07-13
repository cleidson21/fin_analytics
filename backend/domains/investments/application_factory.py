from backend.domains.investments.application.portfolio_dashboard_service import PortfolioDashboardService
from backend.domains.investments.repositories.market_data_repository import MarketDataRepository
from backend.domains.investments.repositories.historical_price_repository import HistoricalPriceRepository
from backend.domains.investments.repositories.trade_repository import TradeRepository
from backend.domains.investments.repositories.snapshot_repository import SnapshotRepository
from backend.domains.investments.repositories.import_log_repository import ImportLogRepository

from backend.domains.investments.engines.position_engine import PositionEngine
from backend.domains.investments.engines.valuation_engine import ValuationEngine
from backend.domains.investments.engines.wealth_engine import WealthEngine
from backend.domains.investments.engines.financial_analytics_engine import FinancialAnalyticsEngine

from backend.domains.investments.services.historical_price_service import HistoricalPriceService
from backend.domains.investments.services.market_data_service import MarketDataService
from backend.domains.investments.services.history_service import HistoryService
from backend.domains.investments.services.parse_service import ParseService
from backend.domains.investments.services.persistence_service import PersistenceService
from backend.domains.investments.services.import_service import ImportService
from backend.domains.investments.services.reconciliation_service import ReconciliationService

from backend.domains.investments.application.portfolio_application_service import PortfolioApplicationService
from backend.domains.investments.application.import_application_service import ImportApplicationService
from backend.domains.investments.application.market_application_service import MarketApplicationService


class ApplicationFactory:
    """
    Factory central (Dependency Injection container).
    Mantém instâncias em cache (Singletons) e constrói a árvore de dependências.
    """
    _instances = {}

    @classmethod
    def _get_or_create(cls, key, factory_func):
        if key not in cls._instances:
            cls._instances[key] = factory_func()
        return cls._instances[key]

    @classmethod
    def get_market_data_repository(cls) -> MarketDataRepository:
        return cls._get_or_create('MarketDataRepository', lambda: MarketDataRepository())

    @classmethod
    def get_historical_price_repository(cls) -> HistoricalPriceRepository:
        return cls._get_or_create('HistoricalPriceRepository', lambda: HistoricalPriceRepository())

    @classmethod
    def get_snapshot_repository(cls) -> SnapshotRepository:
        return cls._get_or_create('SnapshotRepository', lambda: SnapshotRepository())

    @classmethod
    def get_trade_repository(cls) -> TradeRepository:
        return cls._get_or_create('TradeRepository', lambda: TradeRepository())
        
    @classmethod
    def get_import_log_repository(cls) -> ImportLogRepository:
        return cls._get_or_create('ImportLogRepository', lambda: ImportLogRepository())

    @classmethod
    def get_market_data_service(cls) -> MarketDataService:
        return cls._get_or_create('MarketDataService', 
            lambda: MarketDataService(cls.get_market_data_repository()))

    @classmethod
    def get_historical_price_service(cls) -> HistoricalPriceService:
        return cls._get_or_create('HistoricalPriceService', 
            lambda: HistoricalPriceService(cls.get_historical_price_repository()))

    @classmethod
    def get_position_engine(cls) -> PositionEngine:
        return cls._get_or_create('PositionEngine', lambda: PositionEngine())

    @classmethod
    def get_valuation_engine(cls) -> ValuationEngine:
        return cls._get_or_create('ValuationEngine', 
            lambda: ValuationEngine(cls.get_historical_price_service()))

    @classmethod
    def get_wealth_engine(cls) -> WealthEngine:
        return cls._get_or_create('WealthEngine', lambda: WealthEngine())

    @classmethod
    def get_financial_analytics_engine(cls) -> FinancialAnalyticsEngine:
        return cls._get_or_create('FinancialAnalyticsEngine', lambda: FinancialAnalyticsEngine(cls.get_historical_price_service()))

    @classmethod
    def get_history_service(cls) -> HistoryService:
        return cls._get_or_create('HistoryService', lambda: HistoryService(
            pos_engine=cls.get_position_engine(),
            val_engine=cls.get_valuation_engine(),
            wealth_engine=cls.get_wealth_engine(),
            market_service=cls.get_market_data_service()
        ))

    @classmethod
    def get_parse_service(cls) -> ParseService:
        return cls._get_or_create('ParseService', lambda: ParseService())
        
    @classmethod
    def get_persistence_service(cls) -> PersistenceService:
        return cls._get_or_create('PersistenceService', 
            lambda: PersistenceService(cls.get_trade_repository()))

    @classmethod
    def get_import_service(cls) -> ImportService:
        return cls._get_or_create('ImportService', lambda: ImportService(
            parse_service=cls.get_parse_service(),
            persistence_service=cls.get_persistence_service()
        ))

    @classmethod
    def get_reconciliation_service(cls) -> ReconciliationService:
        return cls._get_or_create('ReconciliationService', lambda: ReconciliationService(trade_repo=cls.get_trade_repository(), snapshot_repo=cls.get_snapshot_repository(), position_engine=cls.get_position_engine()))

    # --- APPLICATION SERVICES ---

    @classmethod
    def get_portfolio_application_service(cls) -> PortfolioApplicationService:
        return cls._get_or_create('PortfolioApplicationService', lambda: PortfolioApplicationService(
            position_engine=cls.get_position_engine(),
            valuation_engine=cls.get_valuation_engine(),
            wealth_engine=cls.get_wealth_engine(),
            financial_engine=cls.get_financial_analytics_engine(),
            history_service=cls.get_history_service()
        ))

    @classmethod
    def get_import_application_service(cls) -> ImportApplicationService:
        return cls._get_or_create('ImportApplicationService', lambda: ImportApplicationService(
            import_service=cls.get_import_service(),
            reconciliation_service=cls.get_reconciliation_service(),
            import_log_repo=cls.get_import_log_repository()
        ))

    @classmethod
    def get_market_application_service(cls) -> MarketApplicationService:
        return cls._get_or_create('MarketApplicationService', lambda: MarketApplicationService(
            market_data_service=cls.get_market_data_service(),
            historical_price_service=cls.get_historical_price_service()
        ))

    @classmethod
    def get_portfolio_dashboard_service(cls) -> PortfolioDashboardService:
        return cls._get_or_create('PortfolioDashboardService', lambda: PortfolioDashboardService(
            portfolio_app=cls.get_portfolio_application_service()
        ))
