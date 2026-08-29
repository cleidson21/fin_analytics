"""
ConfirmMyProfitAtivosSyncUseCase

Processa a confirmação de uma importação MYPROFIT_ATIVOS:
1. Valida o SyncLog (existe? é MYPROFIT_ATIVOS? ainda RUNNING?)
2. Valida account_id e reference_date
3. Parseia as staging_rows do provider_metadata
4. Para cada linha: resolve/cria Asset (respeitando Source of Truth)
5. Faz UPSERT de PositionSnapshot (respeitando is_manual)
6. Atualiza SyncLog com status e contadores
7. Retorna relatório detalhado

Tratamento de erros:
- Erros estruturais (SyncLog não existe, conta inválida): aborta tudo (HTTP 4xx)
- Erros de linha individual (ticker inválido, qty=None): registra e continua
- Commit único ao final; rollback em caso de falha não recuperável.
"""

import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from backend.infrastructure.persistence.models.sync_log import SyncLogModel, SyncStatus
from backend.infrastructure.persistence.models.wealth.asset import AssetModel
from backend.infrastructure.persistence.models.wealth.position_snapshot import PositionSnapshotModel


# --------------------------------------------------------------------------
# Helpers de conversão
# --------------------------------------------------------------------------

def _to_decimal(value: Any) -> Optional[Decimal]:
    """Converte float, int ou str para Decimal. Retorna None se inválido."""
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def normalize_myprofit_position(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aplica as regras de negócio para converter um ativo MyProfit para o formato do banco.
    Trata casos específicos como RDB (que não possuem quantidade nominal no CSV).
    """
    ticker = (row.get("ticker") or row.get("ativo") or "").strip()
    sector = (row.get("sector") or row.get("setor") or "").strip() or None
    
    qty = _to_decimal(row.get("quantity"))
    avg_price = _to_decimal(row.get("avg_price"))
    total_investido = _to_decimal(row.get("total_investido"))
    total_atual = _to_decimal(row.get("total_atual"))

    # Default values for normal assets
    normalized = {
        "ticker": ticker,
        "quantity": qty,
        "avg_price": avg_price,
        "current_value": None,
        "sector": sector,
        "asset_class": "STOCK", # Fallback default
        "is_valid": True,
        "error": None
    }
    
    sec_upper = (sector or "").upper()
    if "FUNDO" in sec_upper and "IMOBILI" in sec_upper or "FII" in sec_upper:
        normalized["asset_class"] = "FII"
    elif "BDR" in sec_upper:
        normalized["asset_class"] = "BDR"
    elif "ETF" in sec_upper:
        normalized["asset_class"] = "ETF"
    elif "CRIPTO" in sec_upper:
        normalized["asset_class"] = "CRYPTO"
    elif sec_upper in ["RDB", "TESOURO DIRETO", "RENDA FIXA"]:
        normalized["asset_class"] = "FIXED_INCOME"
    elif not sector:
        normalized["asset_class"] = "OTHER"

    if sector == "RDB":
        normalized["quantity"] = Decimal("1")
        normalized["avg_price"] = total_investido
        normalized["current_value"] = total_atual
        normalized["asset_class"] = "FIXED_INCOME"
    else:
        if normalized["quantity"] is None:
            normalized["is_valid"] = False
            normalized["error"] = f"Quantidade inválida para o ativo não-RDB."

    if not normalized["ticker"]:
        normalized["is_valid"] = False
        normalized["error"] = "Ticker vazio."

    return normalized

# --------------------------------------------------------------------------
# Use Case
# --------------------------------------------------------------------------

class ConfirmMyProfitAtivosSyncUseCase:
    """
    Confirma e persiste uma importação MYPROFIT_ATIVOS.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute(
        self,
        run_id: str,
        account_id: str,
        reference_date: str,
    ) -> Dict[str, Any]:
        """
        Executa a confirmação da importação.

        Args:
            run_id:          ID do SyncLog criado no upload.
            account_id:      ID da conta destino (AccountModel.id).
            reference_date:  Data de referência do snapshot (YYYY-MM-DD).

        Returns:
            Relatório detalhado da importação.

        Raises:
            ValueError: Erro de validação estrutural (não inicia persistência).
        """

        # ------------------------------------------------------------------
        # 1. Carregar e validar o SyncLog
        # ------------------------------------------------------------------
        result = await self.session.execute(
            select(SyncLogModel).where(SyncLogModel.id == run_id)
        )
        sync_log = result.scalar_one_or_none()

        if sync_log is None:
            raise ValueError(f"Importação '{run_id}' não encontrada.")

        if sync_log.provider.value not in ("MYPROFIT_ATIVOS", "MYPROFIT"):
            raise ValueError(
                f"Importação '{run_id}' é do tipo '{sync_log.provider.value}', "
                f"não 'MYPROFIT_ATIVOS'. Este endpoint processa apenas ativos MyProfit."
            )

        if sync_log.status not in (SyncStatus.RUNNING,):
            raise ValueError(
                f"Importação '{run_id}' já foi confirmada ou falhou (status: {sync_log.status.value}). "
                f"Não é possível confirmar novamente."
            )

        # ------------------------------------------------------------------
        # 2. Validar account_id
        # ------------------------------------------------------------------
        # Nota: account_id é validado como string não-vazia.
        # A tabela accounts real usa PK composta (provider+external_id) da fase Pierre,
        # incompatível com AccountModel.id (UUID). A validação de existência de conta
        # ocorre na camada de UI — o usuário seleciona a conta destino antes de confirmar.
        # A integridade referencial é garantida pela chave composta dos snapshots:
        # UNIQUE(account_id, asset_id, reference_date).
        if not account_id or not account_id.strip():
            raise ValueError("account_id é obrigatório e não pode estar vazio.")
        account_id = account_id.strip()

        # ------------------------------------------------------------------
        # 3. Validar reference_date (formato YYYY-MM-DD)
        # ------------------------------------------------------------------
        try:
            datetime.strptime(reference_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                f"Data de referência '{reference_date}' inválida. Use o formato YYYY-MM-DD."
            )

        # ------------------------------------------------------------------
        # 4. Extrair staging_rows do provider_metadata
        # ------------------------------------------------------------------
        metadata = sync_log.provider_metadata or {}
        staging_rows: List[Dict[str, Any]] = metadata.get("staging_rows", [])

        if not staging_rows:
            raise ValueError(
                f"Importação '{run_id}' não possui dados para confirmar. "
                f"O upload pode ter falhado."
            )

        # ------------------------------------------------------------------
        # 5. Processar linhas e persistir
        # ------------------------------------------------------------------
        report = await self._process_rows(
            staging_rows=staging_rows,
            account_id=account_id,
            reference_date=reference_date,
            run_id=run_id,
            source_type=metadata.get("source_type", "MYPROFIT_ATIVOS"),
        )

        # ------------------------------------------------------------------
        # 6. Atualizar SyncLog
        # ------------------------------------------------------------------
        sync_log.status = SyncStatus.SUCCESS if not report["structural_errors"] else SyncStatus.PARTIAL
        sync_log.end_time = datetime.utcnow()
        sync_log.duration_seconds = (
            (sync_log.end_time - sync_log.start_time).total_seconds()
            if sync_log.start_time else None
        )
        sync_log.inserted = report["snapshots_inserted"]
        sync_log.updated = report["snapshots_updated"]
        sync_log.ignored = report["snapshots_preserved_manual"] + report["rows_invalid"]

        # Armazenar relatório completo no metadata
        sync_log.provider_metadata = {
            **metadata,
            "confirmation": {
                "account_id": account_id,
                "reference_date": reference_date,
                "confirmed_at": datetime.utcnow().isoformat(),
            },
            "report": report,
        }

        await self.session.commit()

        return report

    async def _process_rows(
        self,
        staging_rows: List[Dict[str, Any]],
        account_id: str,
        reference_date: str,
        run_id: str,
        source_type: str,
    ) -> Dict[str, Any]:
        """
        Processa cada linha: resolve/cria asset → faz upsert de position_snapshot.
        """

        report: Dict[str, Any] = {
            "total_rows_read": len(staging_rows),
            "rows_valid": 0,
            "rows_invalid": 0,
            "assets_created": 0,
            "assets_reused": 0,
            "snapshots_inserted": 0,
            "snapshots_updated": 0,
            "snapshots_preserved_manual": 0,
            "structural_errors": [],
            "row_errors": [],
            "row_warnings": [],
        }

        for row in staging_rows:
            normalized = normalize_myprofit_position(row)
            ticker = normalized["ticker"]
            
            if not normalized["is_valid"]:
                report["rows_invalid"] += 1
                report["row_errors"].append({
                    "ticker": ticker or "N/A",
                    "error": normalized["error"]
                })
                continue

            report["rows_valid"] += 1

            # ----------------------------------------------------------
            # Resolver ou criar Asset
            # ----------------------------------------------------------
            asset = await self._resolve_asset(
                ticker=ticker, 
                sector=normalized["sector"], 
                asset_class=normalized["asset_class"],
                report=report
            )

            # ----------------------------------------------------------
            # UPSERT de PositionSnapshot
            # ----------------------------------------------------------
            await self._upsert_snapshot(
                account_id=account_id,
                asset_id=asset.id,
                reference_date=reference_date,
                quantity=normalized["quantity"],
                avg_price=normalized["avg_price"],
                current_value=normalized["current_value"],
                run_id=run_id,
                source_type=source_type,
                report=report,
            )

        return report

    async def _resolve_asset(
        self,
        ticker: str,
        sector: Optional[str],
        asset_class: str,
        report: Dict[str, Any],
    ) -> AssetModel:
        """
        Busca o asset pelo ticker.
        - Se existir: enriquece sector/name apenas se estiverem vazios (Source of Truth).
        - Se não existir: cria com os dados disponíveis.
        """
        result = await self.session.execute(
            select(AssetModel).where(AssetModel.ticker == ticker)
        )
        asset = result.scalar_one_or_none()

        if asset is not None:
            # Asset existente — respeitar Source of Truth
            enriched = False
            if not asset.sector and sector:
                asset.sector = sector
                enriched = True
            if enriched:
                asset.updated_at = datetime.utcnow()
            report["assets_reused"] += 1
        else:
            # Criar novo asset com dados básicos do MyProfit
            asset = AssetModel(
                id=str(uuid.uuid4()),
                ticker=ticker,
                name=None,           # nome não está no CSV de ativos; pode vir de seed futuro
                asset_class=asset_class,
                sector=sector,
                currency="BRL",
                source="MYPROFIT_IMPORT",
                is_active=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.session.add(asset)
            await self.session.flush()  # garante que o id está disponível para o FK
            report["assets_created"] += 1

        return asset

    async def _upsert_snapshot(
        self,
        account_id: str,
        asset_id: str,
        reference_date: str,
        quantity: Decimal,
        avg_price: Optional[Decimal],
        current_value: Optional[Decimal],
        run_id: str,
        source_type: str,
        report: Dict[str, Any],
    ) -> None:
        """
        Verifica se existe snapshot para (account_id, asset_id, reference_date).
        - Se não existir: insere (inserted++).
        - Se existir e is_manual=0: atualiza qty e avg_price (updated++).
        - Se existir e is_manual=1: preserva (preserved_manual++, registra warning).
        """
        result = await self.session.execute(
            select(PositionSnapshotModel).where(
                PositionSnapshotModel.account_id == account_id,
                PositionSnapshotModel.asset_id == asset_id,
                PositionSnapshotModel.reference_date == reference_date,
            )
        )
        existing = result.scalar_one_or_none()

        if existing is None:
            # INSERT
            snapshot = PositionSnapshotModel(
                id=str(uuid.uuid4()),
                account_id=account_id,
                asset_id=asset_id,
                reference_date=reference_date,
                quantity=quantity,
                avg_price=avg_price,
                current_value=current_value,
                source_type=source_type,
                run_id=run_id,
                is_manual=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.session.add(snapshot)
            report["snapshots_inserted"] += 1

        elif existing.is_manual == 1:
            # PROTEGIDO — não sobrescrever edição manual
            report["snapshots_preserved_manual"] += 1
            report["row_warnings"].append({
                "asset_id": asset_id,
                "reference_date": reference_date,
                "message": "Snapshot editado manualmente — quantidade preservada.",
                "existing_quantity": str(existing.quantity),
                "imported_quantity": str(quantity),
            })

        else:
            # UPDATE — MyProfit pode sobrescrever
            existing.quantity = quantity
            existing.avg_price = avg_price
            existing.current_value = current_value
            existing.run_id = run_id
            existing.updated_at = datetime.utcnow()
            report["snapshots_updated"] += 1
