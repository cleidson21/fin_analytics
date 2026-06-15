from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Date, Text
from sqlalchemy.orm import relationship
from app.core.db import Base
from datetime import datetime
import uuid

class Benchmark(Base):
    __tablename__ = "benchmarks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    reference_date = Column(Date, nullable=False)
    type = Column(String, nullable=False) # CDI | IBOV | IPCA | S&P500
    value_pct = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Position(Base):
    __tablename__ = "positions"

    ticker = Column(String, primary_key=True)
    data_snapshot = Column(Date, primary_key=True)
    source = Column(String, nullable=False)
    quantidade = Column(Float, nullable=False)
    preco_medio = Column(Float, nullable=False)
    total_investido = Column(Float, nullable=False)
    preco_atual = Column(Float, nullable=False)
    total_atual = Column(Float, nullable=False)
    ganho = Column(Float, nullable=False)
    classe_ativo = Column(String, nullable=True)
    observacao = Column(Text, nullable=True)
    import_run_id = Column(String, ForeignKey("import_runs.id", ondelete="CASCADE"), nullable=False)
    source_line_no = Column(Integer, nullable=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow)

class Dividend(Base):
    __tablename__ = "dividends"

    id_economico = Column(String, primary_key=True)
    source = Column(String, nullable=False)
    ticker = Column(String, nullable=False)
    tipo_evento = Column(String, nullable=False)
    data_pagamento = Column(Date, nullable=False)
    valor_liquido = Column(Float, nullable=False)
    valor_liquido_cents = Column(Integer, nullable=True)
    observacao = Column(Text, nullable=True)
    import_run_id = Column(String, ForeignKey("import_runs.id", ondelete="CASCADE"), nullable=False)
    source_line_no = Column(Integer, nullable=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow)

class PortfolioEvolution(Base):
    __tablename__ = "portfolio_evolution"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reference_month = Column(Date, nullable=False, unique=True)
    rentabilidade_mensal_pct = Column(Float, default=0)
    rentabilidade_acumulada_pct = Column(Float, default=0)
    patrimonio_cents = Column(Integer, nullable=False, default=0)
    compras_cents = Column(Integer, nullable=False, default=0)
    vendas_cents = Column(Integer, nullable=False, default=0)
    op_finalizadas_cents = Column(Integer, nullable=False, default=0)
    proventos_cents = Column(Integer, nullable=False, default=0)
    import_run_id = Column(String, ForeignKey("import_runs.id", ondelete="CASCADE"), nullable=False)
    source_line_no = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
