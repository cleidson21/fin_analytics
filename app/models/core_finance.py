from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Date, Float, Text
from sqlalchemy.orm import relationship
from app.core.db import Base
from datetime import datetime
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default='VIEWER')
    active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

class Category(Base):
    __tablename__ = "categories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    category_type = Column(String, nullable=False) # IN | OUT
    parent_id = Column(String, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    category_id = Column(String, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    expected_amount_cents = Column(Integer, nullable=False)
    billing_cycle = Column(String, nullable=False, default='MONTHLY')
    active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

class Goal(Base):
    __tablename__ = "goals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    category_id = Column(String, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    limit_cents = Column(Integer, nullable=False)
    severity_level = Column(String, nullable=False, default='WARNING') # GOOD | WARNING | DANGER
    active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

class Transaction(Base):
    __tablename__ = "transactions"

    id_economico = Column(String, primary_key=True)
    source = Column(String, nullable=False)
    origin = Column(String, nullable=True)
    domain = Column(String, nullable=True)
    import_run_id = Column(String, ForeignKey("import_runs.id", ondelete="CASCADE"), nullable=False)
    source_line_no = Column(Integer, nullable=True)
    data = Column(Date, nullable=False)
    descricao_original = Column(String, nullable=False)
    descricao_normalizada = Column(String, nullable=False)
    valor = Column(Float, nullable=False)
    valor_cents = Column(Integer, nullable=True)
    identificador_externo = Column(String, nullable=True)
    category_id = Column(String, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=True)
    macro_categoria = Column(String, nullable=True) # Legacy
    sub_categoria = Column(String, nullable=True) # Legacy
    subnatureza = Column(String, nullable=False, default='INDEFINIDO')
    natureza = Column(String, nullable=False)
    perfil = Column(String, nullable=False)
    classificacao_fonte = Column(String, nullable=False, default='ETL')
    applied_rule_id = Column(String, nullable=True)
    parcelamento = Column(String, nullable=True)
    observacao = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow)
