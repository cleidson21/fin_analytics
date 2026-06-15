from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.db import get_db

from app.repositories.core_finance import TransactionRepository, CategoryRepository, GoalRepository, SubscriptionRepository
from app.repositories.wealth import PositionRepository, DividendRepository, PortfolioEvolutionRepository, BenchmarkRepository
from app.repositories.governance import ImportRunRepository, RawEventRepository
from app.repositories.ai_layer import RuleRepository, PromptVersionRepository, AiRunRepository

# Core Finance
def get_transaction_repo() -> TransactionRepository:
    return TransactionRepository()

def get_category_repo() -> CategoryRepository:
    return CategoryRepository()

def get_goal_repo() -> GoalRepository:
    return GoalRepository()

def get_subscription_repo() -> SubscriptionRepository:
    return SubscriptionRepository()

# Wealth
def get_position_repo() -> PositionRepository:
    return PositionRepository()

def get_dividend_repo() -> DividendRepository:
    return DividendRepository()

def get_portfolio_evolution_repo() -> PortfolioEvolutionRepository:
    return PortfolioEvolutionRepository()

def get_benchmark_repo() -> BenchmarkRepository:
    return BenchmarkRepository()

# Governance
def get_import_run_repo() -> ImportRunRepository:
    return ImportRunRepository()

def get_raw_event_repo() -> RawEventRepository:
    return RawEventRepository()

# AI Layer
def get_rule_repo() -> RuleRepository:
    return RuleRepository()

def get_prompt_version_repo() -> PromptVersionRepository:
    return PromptVersionRepository()

def get_ai_run_repo() -> AiRunRepository:
    return AiRunRepository()
