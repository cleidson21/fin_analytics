from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.domains.governance.repository import DashboardRepository, ImportRepository
from backend.domains.governance.dto import DashboardMetricsDTO, ImportRunItemDTO, ImportRunListResponseDTO

class DashboardService:
    def __init__(self, session: Session):
        self.repository = DashboardRepository(session)

    def get_metrics(self) -> DashboardMetricsDTO:
        metrics = self.repository.get_import_metrics()
        # Any business logic combining metrics goes here
        return DashboardMetricsDTO(**metrics)

class ImportService:
    def __init__(self, session: Session):
        self.repository = ImportRepository(session)

    def list_imports(self, limit: int = 10, offset: int = 0) -> ImportRunListResponseDTO:
        raw_items = self.repository.list_import_runs(limit, offset)
        total = self.repository.count_import_runs()
        
        items = [ImportRunItemDTO(**item) for item in raw_items]
        
        return ImportRunListResponseDTO(
            items=items,
            total=total
        )

    def get_import(self, run_id: str) -> ImportRunItemDTO:
        row = self.repository.get_import_run(run_id)
        if not row: return None
        status = row['status']
        if status == 'SUCCESS': front_status = 'CONFIRMED'
        elif status == 'FAILED': front_status = 'FAILED'
        elif status == 'PARTIAL': front_status = 'PARTIAL'
        else: front_status = 'AWAITING_CONFIRMATION'
        return ImportRunItemDTO(
            id=row['id'], source_type=row['source'], file_name=row['filename'] or '',
            started_at=row['started_at'], status=front_status, rows_read=row['rows_parsed'] or 0,
            rows_inserted=row['rows_inserted'] or 0, rows_failed=row['rows_errored'] or 0
        )

    def get_staging_items(self, run_id: str) -> Dict[str, Any]:
        row = self.repository.get_import_run(run_id)
        if not row: return None
        artifacts = self.repository.get_staging_items(run_id)
        import json
        items = []
        for a in artifacts:
            ticker = None
            try:
                data = json.loads(a['raw_data'])
                for key in ['ativo', 'identificador', 'titulo', 'descricao', 'conta']:
                    if key in data: ticker = data[key]; break
            except: pass
            
            v_status = 'VALID'
            if a['status'] == 'ERROR': v_status = 'ERROR'
            elif a['status'] == 'SKIPPED': v_status = 'WARNING'
            elif a['status'] == 'PENDING' and a['error_msg']: v_status = 'ERROR'
            
            items.append({
                'source_line_no': a['row_number'], 'ticker': ticker,
                'validation_status': v_status, 'validation_message': a['error_msg']
            })
        return {'run_id': run_id, 'file_type': row['source'], 'items': items}

    def rollback_import(self, run_id: str):
        self.repository.rollback_import(run_id)
