"""
ConfirmMyProfitProventosSyncUseCase
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
from backend.infrastructure.persistence.models.wealth.income_event import IncomeEventModel
from backend.infrastructure.persistence.models.account import AccountModel


def _to_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


class ConfirmMyProfitProventosSyncUseCase:
    """
    Confirma e persiste uma importação MYPROFIT_PROVENTOS.
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
        """

        result = await self.session.execute(
            select(SyncLogModel).where(SyncLogModel.id == run_id)
        )
        sync_log = result.scalar_one_or_none()

        if sync_log is None:
            raise ValueError(f"Importação '{run_id}' não encontrada.")

        if sync_log.provider.value != "MYPROFIT_PROVENTOS":
            raise ValueError(
                f"Importação '{run_id}' é do tipo '{sync_log.provider.value}', "
                f"não 'MYPROFIT_PROVENTOS'."
            )

        if sync_log.status != SyncStatus.RUNNING:
            raise ValueError(
                f"A importação '{run_id}' não está pendente de confirmação. "
                f"Status atual: {sync_log.status.value}"
            )

        if not account_id:
            raise ValueError("ID da conta (account_id) é obrigatório.")

        metadata = sync_log.provider_metadata or {}
        staging_rows: List[Dict[str, Any]] = metadata.get("staging_rows", [])

        if not staging_rows:
            sync_log.status = SyncStatus.SUCCESS
            sync_log.end_time = datetime.utcnow()
            await self.session.commit()
            return {"run_id": run_id, "processed": 0, "inserted": 0, "updated": 0, "ignored": 0}

        # Cache de ativos para evitar múltiplas consultas
        asset_cache: Dict[str, str] = {}

        inserted_count = 0
        updated_count = 0
        errors = []

        for row in staging_rows:
            ticker = (row.get("ativo") or "").strip()
            if not ticker:
                errors.append("Ativo ausente em uma das linhas.")
                continue

            if ticker not in asset_cache:
                asset_result = await self.session.execute(
                    select(AssetModel).where(AssetModel.ticker == ticker)
                )
                asset_obj = asset_result.scalar_one_or_none()
                if not asset_obj:
                    # Create minimal historical asset record
                    new_asset_id = str(uuid.uuid4())
                    new_asset = AssetModel(
                        id=new_asset_id,
                        ticker=ticker,
                        name=ticker,
                        asset_class="OTHER",
                        currency="BRL",
                        source="MYPROFIT_PROVENTOS",
                        is_active=0,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    self.session.add(new_asset)
                    try:
                        await self.session.flush()
                        asset_cache[ticker] = new_asset_id
                    except Exception as e:
                        errors.append(f"Erro ao criar ativo histórico '{ticker}': {str(e)}")
                        continue
                else:
                    asset_cache[ticker] = asset_obj.id

            asset_id = asset_cache[ticker]
            
            event_type = (row.get("tipo") or "").strip() or "DESCONHECIDO"
            payment_date_str = row.get("data_pgto")
            if not payment_date_str:
                errors.append(f"Data de pagamento ausente para {ticker}.")
                continue
                
            payment_date = datetime.strptime(payment_date_str, "%Y-%m-%d").date()
            
            ex_date_str = row.get("data_com")
            ex_date = datetime.strptime(ex_date_str, "%Y-%m-%d").date() if ex_date_str else None
            
            recebido = _to_decimal(row.get("recebido"))
            cotas = _to_decimal(row.get("cotas"))
            valor_por_cota = _to_decimal(row.get("valor_por_cota"))
            
            if recebido is None or cotas is None or valor_por_cota is None:
                errors.append(f"Valores inválidos (recebido, cotas, valor_por_cota) para {ticker}.")
                continue
                
            yoc = _to_decimal(row.get("yoc"))
            dy = _to_decimal(row.get("dy"))

            # Manual Upsert to handle SQLite NULL comparison limitations
            # Unique identity: account_id, asset_id, event_type, payment_date, ex_date, gross_amount
            conditions = [
                IncomeEventModel.account_id == account_id,
                IncomeEventModel.asset_id == asset_id,
                IncomeEventModel.event_type == event_type,
                IncomeEventModel.payment_date == payment_date,
                IncomeEventModel.gross_amount == recebido,
            ]
            if ex_date:
                conditions.append(IncomeEventModel.ex_date == ex_date)
            else:
                conditions.append(IncomeEventModel.ex_date.is_(None))

            existing_result = await self.session.execute(
                select(IncomeEventModel).where(*conditions)
            )
            existing = existing_result.scalar_one_or_none()

            try:
                if existing:
                    existing.quantity = cotas
                    existing.value_per_unit = valor_por_cota
                    existing.yoc = yoc
                    existing.dy = dy
                    existing.run_id = run_id
                    existing.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
                    new_event = IncomeEventModel(
                        id=str(uuid.uuid4()),
                        account_id=account_id,
                        asset_id=asset_id,
                        event_type=event_type,
                        payment_date=payment_date,
                        ex_date=ex_date,
                        quantity=cotas,
                        value_per_unit=valor_por_cota,
                        gross_amount=recebido,
                        yoc=yoc,
                        dy=dy,
                        run_id=run_id,
                        source_type="MYPROFIT_PROVENTOS",
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    self.session.add(new_event)
                    inserted_count += 1
            except Exception as e:
                errors.append(f"Erro ao inserir/atualizar provento de {ticker}: {str(e)}")

        if errors:
            sync_log.status = SyncStatus.FAILED
            sync_log.error_message = f"Encontrados {len(errors)} erros na confirmação."
            sync_log.end_time = datetime.utcnow()
            metadata["confirmation_errors"] = errors
            sync_log.provider_metadata = metadata
            await self.session.commit()
            
            error_details = "; ".join(errors[:5])
            if len(errors) > 5:
                error_details += f" ... e mais {len(errors)-5} erros."
            raise ValueError(f"Erro ao processar proventos: {error_details}")

        sync_log.status = SyncStatus.SUCCESS
        sync_log.inserted = inserted_count
        sync_log.updated = updated_count
        sync_log.end_time = datetime.utcnow()
        await self.session.commit()

        return {
            "run_id": run_id,
            "processed": len(staging_rows),
            "inserted": inserted_count,
            "updated": updated_count,
            "ignored": 0
        }
