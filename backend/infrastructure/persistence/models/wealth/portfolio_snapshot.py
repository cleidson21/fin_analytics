import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric
from backend.database.base import Base

class PortfolioSnapshotModel(Base):
    """
    Evolução patrimonial mensal da carteira.
    
    Identidade lógica: UNIQUE(account_id, reference_month)
    - account_id + reference_month = identidade única do mês.
    - Mesma combinação → UPSERT (atualiza valores).
    - Mês diferente → novo snapshot, preservando os meses anteriores.
    """
    __tablename__ = "portfolio_snapshots"

    account_id = Column(String(36), primary_key=True)
    reference_month = Column(String(7), primary_key=True)  # Formato YYYY-MM
    
    patrimonio = Column(Numeric(18, 2), nullable=False)
    pct_mensal = Column(Numeric(10, 4), nullable=True)     # Salva como decimal: 5.45% -> 0.0545
    pct_acumulada = Column(Numeric(10, 4), nullable=True)  
    
    compras = Column(Numeric(18, 2), nullable=True)
    vendas = Column(Numeric(18, 2), nullable=True)
    op_finalizadas = Column(Numeric(18, 2), nullable=True)
    proventos = Column(Numeric(18, 2), nullable=True)
    
    # Benchmarks (Mensal e Acumulado) - salvos como decimal: 5.45% -> 0.0545
    ibov_mensal = Column(Numeric(10, 4), nullable=True)
    ibov_acumulado = Column(Numeric(10, 4), nullable=True)
    cdi_mensal = Column(Numeric(10, 4), nullable=True)
    cdi_acumulado = Column(Numeric(10, 4), nullable=True)
    ipca_mensal = Column(Numeric(10, 4), nullable=True)
    ipca_acumulado = Column(Numeric(10, 4), nullable=True)
    ifix_mensal = Column(Numeric(10, 4), nullable=True)
    ifix_acumulado = Column(Numeric(10, 4), nullable=True)
    sp_mensal = Column(Numeric(10, 4), nullable=True)
    sp_acumulado = Column(Numeric(10, 4), nullable=True)
    idiv_mensal = Column(Numeric(10, 4), nullable=True)
    idiv_acumulado = Column(Numeric(10, 4), nullable=True)

    run_id = Column(String(36), nullable=True)
    source_type = Column(String(64), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
