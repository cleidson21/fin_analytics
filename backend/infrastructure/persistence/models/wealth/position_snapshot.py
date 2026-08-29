import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Integer, ForeignKey, UniqueConstraint
from backend.database.base import Base


class PositionSnapshotModel(Base):
    """
    Estado patrimonial de um ativo em uma data específica.

    Identidade lógica: UNIQUE(account_id, asset_id, reference_date)
    - account_id + asset_id + reference_date = identidade única de posição.
    - Mesma combinação → UPSERT (nunca duplicação).
    - Nova reference_date → novo snapshot, preservando os anteriores.
    - Ausência de ativo num novo CSV nunca apaga snapshots anteriores.

    Estratégia de proteção manual:
    - is_manual = 0: MyProfit pode atualizar quantity e avg_price.
    - is_manual = 1: MyProfit NÃO sobrescreve; ocorrência registrada no log.

    Precisão de quantidade:
    - Numeric(18, 8) armazena até 8 casas decimais (suficiente para BTC: 0.0014,
      Tesouro: 0.24, ações inteiras: 552).
    - Evita erros de float. A camada de leitura retorna Decimal.

    avg_price:
    - Campo referencial proveniente do MyProfit ("Preço médio").
    - Numeric(18, 6) em BRL (centavos não são necessários pois já é decimal).
    - Nullable: ausente quando coluna "Preço médio" não está no CSV.
    - NÃO é cotação atual; é preço médio de compra informado pelo MyProfit.
    """
    __tablename__ = "position_snapshots"
    __table_args__ = (
        UniqueConstraint("account_id", "asset_id", "reference_date",
                         name="uq_position_snapshot_account_asset_date"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Reference to accounts.id (validated programmatically; no FK constraint due to
    # dual-schema accounts table in live DB — logical reference only)
    account_id = Column(String(36), nullable=False, index=True)

    # FK para assets.id (AssetModel — criado nesta Fase 1)
    asset_id = Column(String(36), ForeignKey("assets.id"), nullable=False, index=True)

    # Data do snapshot informada pelo usuário na UI (formato YYYY-MM-DD)
    reference_date = Column(String(10), nullable=False, index=True)

    # Quantidade do ativo na data do snapshot
    # Numeric(18, 8): suporta BTC com 8 casas, Tesouro com frações, ações inteiras.
    quantity = Column(Numeric(18, 8), nullable=False)

    # Preço médio de compra informado pelo MyProfit (opcional, BRL decimal)
    avg_price = Column(Numeric(18, 6), nullable=True)

    # Valor atual explícito (market value) informado pelo MyProfit, útil p/ RDB
    current_value = Column(Numeric(18, 2), nullable=True)

    # Fonte do registro: MYPROFIT_ATIVOS | MYPROFIT_EVOLUCAO | MANUAL | etc.
    source_type = Column(String, nullable=False, default="MYPROFIT_ATIVOS")

    # FK lógica para sync_logs.id (auditoria da importação)
    run_id = Column(String(36), nullable=True, index=True)

    # Proteção de edição manual: 0 = MyProfit pode atualizar; 1 = preservar
    is_manual = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
