from sqlalchemy import Column, String, Integer, Float
from backend.shared.db import Base
from datetime import datetime
import uuid

class Dividend(Base):
    __tablename__ = "dividends"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = Column(String, nullable=False)
    account_id = Column(String, nullable=False)
    type = Column(String, nullable=False)
    currency = Column(String, nullable=False, default='BRL')
    ex_date = Column(String, nullable=False)
    payment_date = Column(String, nullable=False)
    quantity_held = Column(Float, nullable=False)
    value_per_share = Column(Integer, nullable=False)
    gross_amount = Column(Integer, nullable=False)
    irrf_tax = Column(Integer, nullable=False, default=0)
    transaction_id = Column(String, nullable=True)
    source = Column(String, nullable=False)
    run_id = Column(String, nullable=True)
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat() + "Z")

class PositionSnapshot(Base):
    __tablename__ = "position_snapshots"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    snapshot_hash = Column(String, unique=True, nullable=False)
    reference_date = Column(String, nullable=False)
    ticker = Column(String, nullable=False)
    asset_type = Column(String, nullable=False)
    institution = Column(String, nullable=False)
    source_system = Column(String, nullable=False, default='B3_AREA_INVESTIDOR')
    quantity = Column(Float, nullable=False)
    unit_price = Column(String, nullable=True)
    total_value = Column(String, nullable=True)
    metadata_json = Column(String, nullable=False, default='{}')
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at = Column(String, default=lambda: datetime.utcnow().isoformat() + "Z")
    run_id = Column(String, nullable=True)

class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    date = Column(String, nullable=False)
    total_equity = Column(Integer, nullable=False)
    cost_basis = Column(Integer, nullable=False)
    total_deposits = Column(Integer, nullable=False, default=0)
    total_withdrawals = Column(Integer, nullable=False, default=0)
    quota_value = Column(Float, nullable=False, default=1.0)
    daily_twr = Column(Float, default=0.0)
    monthly_twr = Column(Float, default=0.0)
    cumulative_twr = Column(Float, default=0.0)
    mwr = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    sortino_ratio = Column(Float, nullable=True)
    beta_ibov = Column(Float, nullable=True)
    alpha_ibov = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    volatility_annual = Column(Float, nullable=True)
    ibov_cumulative = Column(Float, nullable=True)
    cdi_cumulative = Column(Float, nullable=True)
    ifix_cumulative = Column(Float, nullable=True)
    spx_cumulative = Column(Float, nullable=True)
    dividends_month = Column(Integer, default=0)
    dividends_year = Column(Integer, default=0)
    dividends_total = Column(Integer, default=0)
    computed_at = Column(String, default=lambda: datetime.utcnow().isoformat() + "Z")
    run_id = Column(String, nullable=True)
