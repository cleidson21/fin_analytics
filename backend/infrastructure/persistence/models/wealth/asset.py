import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, DateTime, Numeric, Integer, Index, UniqueConstraint
from backend.database.base import Base


class AssetModel(Base):
    """
    Catálogo mestre de ativos investíveis.

    Identidade única: ticker (UNIQUE).
    Um ativo é identificado pelo seu código de mercado.

    Regras de enriquecimento pelo MyProfit:
    - sector: pode ser preenchido SOMENTE se estiver vazio no banco.
    - name:   pode ser preenchido SOMENTE se estiver vazio no banco.
    - asset_class: não sobrescrever se já existir classificação consolidada.
    """
    __tablename__ = "assets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    ticker = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=True)

    # STOCK | FII | BDR | ETF | STOCK_US | FIXED_INCOME | CRYPTO | OTHER
    asset_class = Column(String, nullable=False, default="OTHER")

    # Setor (ex: Papeis, Shoppings, Petróleo, Tesouro Direto, RDB, Criptomoeda)
    sector = Column(String, nullable=True)

    currency = Column(String, nullable=False, default="BRL")

    # Ticker como yfinance conhece (ex: "BBAS3.SA", "BTC-USD")
    yfinance_ticker = Column(String, nullable=True)

    # Origem do registro: MANUAL | MYPROFIT_IMPORT | SEED | SYSTEM
    source = Column(String, nullable=False, default="MYPROFIT_IMPORT")

    is_active = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
