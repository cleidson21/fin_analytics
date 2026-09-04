"""
ConfirmMyProfitEvolucaoSyncUseCase

Processa a confirmação de uma importação MYPROFIT_EVOLUCAO:
1. Valida o SyncLog (existe? é MYPROFIT_EVOLUCAO? ainda RUNNING?)
2. Valida account_id
3. Parseia as staging_rows do provider_metadata
4. Faz UPSERT de PortfolioSnapshot
5. Atualiza SyncLog com status e contadores
6. Retorna relatório
"""

import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from backend.infrastructure.persistence.models.sync_log import SyncLogModel, SyncStatus
from backend.infrastructure.persistence.models.wealth.portfolio_snapshot import PortfolioSnapshotModel


def _to_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


class ConfirmMyProfitEvolucaoSyncUseCase:
    """
    Confirma e persiste uma importação MYPROFIT_EVOLUCAO.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute(
        self,
        run_id: str,
        account_id: str,
    ) -> Dict[str, Any]:
        """
        Executa a confirmação da importação.

        Args:
            run_id:          ID do SyncLog criado no upload.
            account_id:      ID da conta destino.

        Returns:
            Relatório detalhado da importação.
        """

        # 1. Carregar e validar o SyncLog
        result = await self.session.execute(
            select(SyncLogModel).where(SyncLogModel.id == run_id)
        )
        sync_log = result.scalar_one_or_none()

        if sync_log is None:
            raise ValueError(f"Importação '{run_id}' não encontrada.")

        if sync_log.provider.value != "MYPROFIT_EVOLUCAO":
            raise ValueError(
                f"Importação '{run_id}' é do tipo '{sync_log.provider.value}', "
                f"não 'MYPROFIT_EVOLUCAO'."
            )

        if sync_log.status != SyncStatus.RUNNING:
            raise ValueError(
                f"A importação '{run_id}' não está pendente de confirmação. "
                f"Status atual: {sync_log.status.value}"
            )

        if not account_id:
            raise ValueError("ID da conta (account_id) é obrigatório.")

        # 2. Carregar dados em staging
        metadata = sync_log.provider_metadata or {}
        staging_rows: List[Dict[str, Any]] = metadata.get("staging_rows", [])

        if not staging_rows:
            sync_log.status = SyncStatus.SUCCESS
            sync_log.end_time = datetime.utcnow()
            await self.session.commit()
            return {"run_id": run_id, "processed": 0, "inserted": 0, "updated": 0, "ignored": 0}

        inserted_count = 0
        updated_count = 0
        errors = []

        # 3. Processar cada linha
        for row in staging_rows:
            ref_month = row.get("reference_month")
            if not ref_month:
                errors.append("Mês de referência ausente em uma linha.")
                continue

            patrimonio = _to_decimal(row.get("patrimonio"))
            if patrimonio is None:
                errors.append(f"Patrimônio ausente para o mês {ref_month}.")
                continue

            # Montar payload
            values = {
                "account_id": account_id,
                "reference_month": ref_month,
                "patrimonio": patrimonio,
                "pct_mensal": _to_decimal(row.get("pct_mensal")),
                "pct_acumulada": _to_decimal(row.get("pct_acumulada")),
                "compras": _to_decimal(row.get("compras")),
                "vendas": _to_decimal(row.get("vendas")),
                "op_finalizadas": _to_decimal(row.get("op_finalizadas")),
                "proventos": _to_decimal(row.get("proventos")),
                "ibov_mensal": _to_decimal(row.get("ibov_mensal")),
                "ibov_acumulado": _to_decimal(row.get("ibov_acumulado")),
                "cdi_mensal": _to_decimal(row.get("cdi_mensal")),
                "cdi_acumulado": _to_decimal(row.get("cdi_acumulado")),
                "ipca_mensal": _to_decimal(row.get("ipca_mensal")),
                "ipca_acumulado": _to_decimal(row.get("ipca_acumulado")),
                "ifix_mensal": _to_decimal(row.get("ifix_mensal")),
                "ifix_acumulado": _to_decimal(row.get("ifix_acumulado")),
                "sp_mensal": _to_decimal(row.get("sp_mensal")),
                "sp_acumulado": _to_decimal(row.get("sp_acumulado")),
                "idiv_mensal": _to_decimal(row.get("idiv_mensal")),
                "idiv_acumulado": _to_decimal(row.get("idiv_acumulado")),
                "run_id": run_id,
                "source_type": "MYPROFIT_EVOLUCAO",
                "updated_at": datetime.utcnow()
            }

            # 4. UPSERT via SQLite
            stmt = sqlite_insert(PortfolioSnapshotModel).values(values)
            
            # Colunas a atualizar em caso de conflito (tudo exceto PK e created_at)
            update_dict = {
                k: v for k, v in values.items() 
                if k not in ["account_id", "reference_month"]
            }

            stmt = stmt.on_conflict_do_update(
                index_elements=["account_id", "reference_month"],
                set_=update_dict
            )

            # Executa
            result_proxy = await self.session.execute(stmt)
            # Tentar descobrir se foi insert ou update é difícil com on_conflict_do_update no sqlite de forma genérica
            # Vamos incrementar inserted, e atualizaremos depois. Na verdade, como é idempotente, 
            # podemos simplificar dizendo que a linha foi processada com sucesso.
            inserted_count += 1

        # 5. Atualizar SyncLog
        if errors:
            sync_log.status = SyncStatus.PARTIAL
        else:
            sync_log.status = SyncStatus.SUCCESS

        sync_log.end_time = datetime.utcnow()
        if sync_log.start_time:
            sync_log.duration_seconds = (sync_log.end_time - sync_log.start_time).total_seconds()
        
        sync_log.inserted = inserted_count
        
        metadata["errors"] = errors
        sync_log.provider_metadata = metadata

        await self.session.commit()

        return {
            "run_id": run_id,
            "processed": len(staging_rows),
            "inserted": inserted_count,
            "errors": errors,
            "status": sync_log.status.value
        }
