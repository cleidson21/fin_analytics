from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, func

from backend.infrastructure.persistence.models.sync_log import SyncLogModel, SyncStatus

class GetGovernanceDashboardUseCase:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute(self) -> Dict[str, Any]:
        result = await self.session.execute(select(SyncLogModel))
        logs = list(result.scalars().all())
        
        total_runs = len(logs)
        confirmed_runs = sum(1 for log in logs if log.status == SyncStatus.SUCCESS)
        pending_runs = sum(1 for log in logs if log.status == SyncStatus.RUNNING)
        lines_inserted = sum(log.inserted for log in logs if log.inserted)
        lines_updated = sum(log.updated for log in logs if log.updated)
        lines_failed = sum(1 for log in logs if log.status == SyncStatus.FAILED)
        
        last_import = None
        if logs:
            sorted_logs = sorted(logs, key=lambda x: x.start_time, reverse=True)
            last_import = sorted_logs[0].start_time.isoformat() if sorted_logs[0].start_time else None
            
        return {
            "total_runs": total_runs,
            "confirmed_runs": confirmed_runs,
            "pending_runs": pending_runs,
            "lines_inserted": lines_inserted,
            "lines_updated": lines_updated,
            "lines_failed": lines_failed,
            "last_import": last_import
        }

class GetGovernanceImportsUseCase:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute(self, limit: int = 10) -> Dict[str, Any]:
        result = await self.session.execute(
            select(SyncLogModel).order_by(desc(SyncLogModel.start_time)).limit(limit)
        )
        logs = list(result.scalars().all())
        
        count_result = await self.session.execute(select(func.count(SyncLogModel.id)))
        total = count_result.scalar() or 0
        
        items = []
        for log in logs:
            items.append({
                "id": log.id,
                "source_type": log.provider.value,
                "file_name": "API Pierre" if log.provider.value == "PIERRE" else "Upload",
                "started_at": log.start_time.isoformat() if log.start_time else "",
                "status": log.status.value,
                "rows_read": log.transactions_synced or 0,
                "rows_inserted": log.inserted or 0,
                "rows_failed": 1 if log.status == SyncStatus.FAILED else 0
            })
            
        return {
            "items": items,
            "total": total
        }

class UploadImportUseCase:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute(self, user_id: str, source_type: str, file_content: bytes, filename: str) -> Dict[str, Any]:
        from backend.infrastructure.persistence.models.sync_log import SyncStatus
        from backend.domain.enums.provider_type import ProviderType
        from backend.integrations.myprofit.parser import MyProfitParser

        # Mapear source_type para o ProviderType correspondente
        try:
            provider = ProviderType(source_type)
        except ValueError:
            # Fallback: se não existir no enum, usar MYPROFIT para tipos MYPROFIT_*
            provider = ProviderType.MYPROFIT if source_type.startswith("MYPROFIT") else ProviderType.CSV

        try:
            parser = MyProfitParser(file_content)

            if source_type == "MYPROFIT_ATIVOS":
                # Validação de headers + filtragem de linha de totais
                rows, parse_report = parser.parse_ativos()

                if parse_report.get("errors"):
                    raise ValueError(
                        f"Arquivo incompatível com o tipo {source_type}: "
                        + "; ".join(parse_report["errors"])
                    )
            else:
                # Modo genérico para outros tipos (backward compatibility)
                rows = parser.parse()
                parse_report = {
                    "total_rows": len(rows),
                    "valid_rows": len(rows),
                    "errors": [],
                    "warnings": [],
                }

        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Erro ao parsear arquivo: {str(e)}")

        log = SyncLogModel(
            user_id=str(user_id) if user_id else None,
            provider=provider,
            status=SyncStatus.RUNNING,
            transactions_synced=len(rows),
            provider_metadata={
                "source_type": source_type,
                "filename": filename,
                "staging_rows": rows,
                "parse_report": parse_report,
            }
        )
        self.session.add(log)
        await self.session.commit()

        return {
            "run_id": log.id,
            "preview": {
                "detected_file_type": source_type,
                "total_rows": parse_report.get("total_rows", len(rows)),
                "valid_rows": len(rows),
                "invalid_rows": parse_report.get("total_rows", len(rows)) - len(rows),
                "errors": parse_report.get("errors", []),
                "warnings": parse_report.get("warnings", []),
                "columns": {
                    "required": parse_report.get("required_columns", []),
                    "optional": parse_report.get("optional_columns", []),
                    "missing": parse_report.get("missing_columns", []),
                    "ignored": parse_report.get("ignored_columns", []),
                },
            }
        }
