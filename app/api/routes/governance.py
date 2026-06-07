from decimal import Decimal
import hashlib
import os
from datetime import datetime
import uuid

from fastapi import APIRouter, HTTPException

from app.api.schemas.governance import (
    ImportStatusResponse,
    PierreImportPreview,
    PierreImportRequest,
    PierreImportResponse,
    QuarantineTransaction,
    ImportRunListResponse,
    ImportRunItem,
    MyProfitImportRequest,
    MyProfitImportResponse,
    MyProfitPreview,
    DashboardMetricsResponse,
)
from app.api.services.pierre_parser import PierreParser
from app.api.services.myprofit_parser import MyProfitParser, EmptyFileException, AmbiguousFileException
from database.repository import DatabaseManager
from database.queries import FinancialQueries

from fastapi import APIRouter, HTTPException, Depends
from app.api.deps import require_admin

router = APIRouter(dependencies=[Depends(require_admin)])
queries = FinancialQueries()
repository = DatabaseManager()
parser = PierreParser()
myprofit_parser = MyProfitParser()


from app.api.schemas.admin import (
    AuditLogResponse, 
    AuditLogDetailResponse,
    TransactionUpdateRequest,
    PositionUpdateRequest,
    DividendUpdateRequest,
    CategoryMergeRequest
)

def _save_import_artifact(raw_text: str, source_type: str, run_id: str) -> str:
    """Saves the raw text to archive/imports/YYYY-MM/ and returns the relative path."""
    now = datetime.now()
    month_folder = now.strftime("%Y-%m")
    base_path = os.path.join("archive", "imports", month_folder)
    os.makedirs(base_path, exist_ok=True)
    
    file_extension = "csv" if source_type == "MYPROFIT" else "txt"
    file_name = f"{source_type.lower()}_{run_id}_{now.strftime('%Y%m%d_%H%M%S')}.{file_extension}"
    full_path = os.path.join(base_path, file_name)
    
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(raw_text)
        
    return full_path.replace("\\", "/")

@router.get("/audit-logs", response_model=list[AuditLogResponse])
def list_audit_logs(
    entity_type: str = None, 
    action: str = None, 
    changed_by: str = None, 
    start_date: str = None,
    end_date: str = None,
    limit: int = 100, 
    offset: int = 0
):
    """Lista o log de auditoria histórico."""
    return queries.get_audit_logs(entity_type, action, changed_by, start_date, end_date, limit, offset)

@router.get("/audit-logs/{log_id}", response_model=AuditLogDetailResponse)
def get_audit_log(log_id: str):
    """Obtém detalhes de um registro de auditoria."""
    log = queries.get_audit_log_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Audit log não encontrado")
    return log


@router.get("/quarantine", response_model=list[QuarantineTransaction])
def get_quarantine():
    """Retorna as transações pendentes de taxonomia (OUTROS/INDEFINIDO)."""
    df = queries.get_quarantine_transactions()
    if df.empty:
        return []

    df["data"] = df["data"].astype(str)
    records = df.to_dict(orient="records")

    for record in records:
        record["valor"] = Decimal(str(record["valor"]))

    return records


@router.get("/import-status", response_model=ImportStatusResponse)
def get_import_status():
    """Retorna o estado operacional da importação do Pierre."""
    return queries.get_import_status()


@router.post("/import-pierre", response_model=PierreImportResponse)
def import_pierre(payload: PierreImportRequest):
    raw_text = payload.raw_text or ""
    checksum = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

    run_id = repository.create_import_run(
        source_type="PIERRE",
        file_name="import_api.txt",
        checksum=checksum,
        status="PENDING",
        created_by="api_user"
    )
    
    saved_path = _save_import_artifact(raw_text, "PIERRE", run_id)
    
    repository.create_import_artifact(
        import_run_id=run_id,
        artifact_type="PIERRE_MSG",
        storage_path=saved_path,
        sha256=checksum,
        size_bytes=len(raw_text.encode("utf-8")),
        mime_type="text/plain"
    )

    try:
        repository.update_import_run_status(run_id, "PROCESSING")
        
        staged_items = parser.parse(raw_text)
        rows_read = len(staged_items)
        
        repository.insert_staging_items(run_id, staged_items)
        processed_preview = repository.process_staging_to_transactions(run_id)
        
        rows_failed = sum(1 for item in processed_preview if item.get("status") in ("ERROR", "DUPLICATE"))
        rows_inserted = sum(1 for item in processed_preview if item.get("status") == "IMPORTED")
        
        if rows_inserted == 0 and rows_read > 0:
            final_status = "FAILED"
        elif rows_failed > 0:
            final_status = "PARTIAL"
        else:
            final_status = "SUCCESS"
            
        repository.update_import_run_metrics(
            run_id=run_id,
            status=final_status,
            rows_read=rows_read,
            rows_inserted=rows_inserted,
            rows_failed=rows_failed
        )
    except Exception as e:
        repository.update_import_run_metrics(
            run_id=run_id,
            status="FAILED",
            rows_read=0,
            rows_inserted=0,
            rows_failed=0,
            error_log=str(e)
        )
        raise

    preview_items = [
        {
            "date": str(item.get("date", "")),
            "description": str(item.get("description", "")),
            "amount": Decimal(str(item.get("amount", 0))),
            "status": str(item.get("status", "PENDING")),
        }
        for item in processed_preview[:5]
    ]

    return PierreImportResponse(
        run_id=run_id,
        preview=PierreImportPreview(items=preview_items),
    )


@router.get("/imports", response_model=ImportRunListResponse)
def get_imports(limit: int = 50, offset: int = 0):
    """Retorna o histórico de importações registradas em import_runs."""
    df = queries.get_import_runs(limit=limit, offset=offset)
    if df.empty:
        return ImportRunListResponse(items=[], total=0)
        
    import pandas as pd
    records = [{k: v if pd.notna(v) else None for k, v in row.items()} for row in df.to_dict(orient="records")]
    return ImportRunListResponse(
        items=records,
        total=len(records) # ideal seria um count real
    )

@router.get("/dashboard", response_model=DashboardMetricsResponse)
def get_dashboard_metrics():
    """Retorna KPIs para o dashboard de importações."""
    return queries.get_dashboard_metrics()

@router.get("/imports/{run_id}")
def get_import_run(run_id: str):
    """Retorna os detalhes de uma import_run específica."""
    run_details = queries.get_import_run_by_id(run_id)
    if not run_details:
        return {"error": "Run not found"}
    return run_details

@router.post("/imports/{run_id}/confirm")
def confirm_import_run(run_id: str):
    """Confirma a importação, promovendo de Staging para as tabelas finais de forma atômica."""
    
    # 1. Lock Lógico atômico (evita race condition de duplo clique)
    locked = repository.lock_import_run_for_confirmation(run_id)
    if not locked:
        run_details = queries.get_import_run_by_id(run_id)
        if not run_details:
            raise HTTPException(status_code=404, detail="Run not found")
        raise HTTPException(status_code=400, detail=f"Import run cannot be confirmed from status {run_details.get('status', 'UNKNOWN')}")
        
    try:
        # 2. Promoção Atômica (tudo ou nada)
        result = repository.promote_all_wealth_staging(run_id)
        return {"message": "Importação confirmada e persistida com sucesso.", "inserted": result["inserted"]}
    except Exception as e:
        # Em caso de crash do banco, aborta
        repository.update_import_run_status(run_id, "FAILED")
        raise HTTPException(status_code=500, detail=f"Erro interno de persistência: {str(e)}")


@router.post("/imports/{run_id}/reprocess")
def reprocess_import(run_id: str):
    """Reprocessa um import existente usando o artifact salvo no filesystem."""
    run_details = queries.get_import_run_by_id(run_id)
    if not run_details:
        raise HTTPException(status_code=404, detail="Run not found")
        
    with repository._get_connection() as conn:
        artifact = conn.execute(
            "SELECT storage_path FROM import_artifacts WHERE import_run_id = ? ORDER BY created_at DESC LIMIT 1",
            (run_id,)
        ).fetchone()
        
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact não encontrado para este run")
        
    storage_path = artifact["storage_path"]
    
    if not os.path.exists(storage_path):
        raise HTTPException(status_code=404, detail="Arquivo físico original não encontrado no disco")
        
    with open(storage_path, "r", encoding="utf-8") as f:
        raw_text = f.read()
        
    source_type = run_details["source_type"]
    
    # Reutiliza os endpoints existentes que processam o texto bruto
    if source_type == "PIERRE":
        req = PierreImportRequest(raw_text=raw_text)
        return import_pierre(req)
    elif source_type == "MYPROFIT":
        file_name = run_details.get("file_name", "reprocess.csv")
        req = MyProfitImportRequest(raw_text=raw_text, file_name=file_name)
        return import_myprofit(req)
    else:
        raise HTTPException(status_code=400, detail=f"Reprocessamento não suportado para o source_type: {source_type}")


@router.post("/imports/{run_id}/rollback")
def rollback_import_run(run_id: str):
    """Remove completamente todos os vestígios de uma importação."""
    run_details = queries.get_import_run_by_id(run_id)
    if not run_details:
        raise HTTPException(status_code=404, detail="Run not found")
        
    try:
        with repository._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM positions WHERE import_run_id = ?", (run_id,))
            cursor.execute("DELETE FROM dividends WHERE import_run_id = ?", (run_id,))
            cursor.execute("DELETE FROM portfolio_evolution WHERE import_run_id = ?", (run_id,))
            cursor.execute("DELETE FROM transactions WHERE import_run_id = ?", (run_id,))
            
            # Deletar import_runs dispara o CASCADE que limpa staging e artifacts
            cursor.execute("DELETE FROM import_runs WHERE id = ?", (run_id,))
            conn.commit()
            
        return {"message": "Rollback concluído. Todos os dados e staging foram expurgados."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no rollback: {str(e)}")

@router.get("/imports/{run_id}/staging-items")
def get_staging_items(run_id: str):
    """Busca os itens reais carregados na Staging Area."""
    run_details = queries.get_import_run_by_id(run_id)
    if not run_details:
        raise HTTPException(status_code=404, detail="Run not found")
        
    staging_data = queries.get_wealth_staging_items(run_id)
    return staging_data

@router.post("/import-myprofit", response_model=MyProfitImportResponse)
def import_myprofit(payload: MyProfitImportRequest):
    raw_text = payload.raw_text or ""
    file_name = payload.file_name or "unknown.csv"
    checksum = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

    run_id = repository.create_import_run(
        source_type="MYPROFIT",
        file_name=file_name,
        checksum=checksum,
        status="PENDING",
        created_by="api_user"
    )
    
    saved_path = _save_import_artifact(raw_text, "MYPROFIT", run_id)
    
    repository.create_import_artifact(
        import_run_id=run_id,
        artifact_type="MYPROFIT_CSV",
        storage_path=saved_path,
        sha256=checksum,
        size_bytes=len(raw_text.encode("utf-8")),
        mime_type="text/csv"
    )

    try:
        repository.update_import_run_status(run_id, "PROCESSING")
        
        # Validar duplicação de checksum na tabela import_runs
        # (Opcional: Fazer uma query pra isso)
        # O user disse "verificar colisão", como é apenas preview, vamos simplificar.

        preview_data = myprofit_parser.parse_preview(raw_text)
        
        file_type = preview_data.get("file_type")
        parsed_items = preview_data.pop("parsed_items", [])
        
        # 1. Staging Insert
        repository.insert_wealth_staging_items(run_id, file_type, parsed_items)
        
        # 2. Classificação UNCHANGED / UPDATE / VALID
        conflict_counts = repository.mark_staging_conflicts(run_id, file_type)
        preview_data["conflicts"] = conflict_counts.get("conflicts", 0)
        preview_data["unchanged"] = conflict_counts.get("unchanged", 0)
        preview_data["updates"] = conflict_counts.get("update", 0)
        
        # 3. Save PREVIEW_SUMMARY
        import json
        preview_json = json.dumps(preview_data, ensure_ascii=False)
        
        final_status = "AWAITING_CONFIRMATION"
        if preview_data.get("errors", 0) == preview_data.get("total_rows", 0) and preview_data.get("total_rows", 0) > 0:
            final_status = "FAILED"
            
        repository.update_import_run_metrics(
            run_id=run_id,
            status=final_status,
            rows_read=preview_data.get("total_rows", 0),
            rows_inserted=0,
            rows_failed=preview_data.get("errors", 0),
            error_log=None,
            preview_summary=preview_json
        )
        
        # Adaptação para o schema do Preview
        return MyProfitImportResponse(
            run_id=run_id,
            preview=MyProfitPreview(
                source_type="MYPROFIT",
                detected_file_type=file_type or "UNKNOWN",
                tickers_found=preview_data.get("tickers_found", []),
                total_rows=preview_data.get("total_rows", 0),
                period_start=preview_data.get("period_start"),
                period_end=preview_data.get("period_end"),
                warnings=preview_data.get("warnings", 0),
                errors=preview_data.get("errors", 0)
            )
        )
        
    except (EmptyFileException, AmbiguousFileException) as e:
        repository.update_import_run_metrics(
            run_id=run_id,
            status="FAILED",
            rows_read=0,
            rows_inserted=0,
            rows_failed=0,
            error_log=str(e)
        )
        raise
    except Exception as e:
        repository.update_import_run_metrics(
            run_id=run_id,
            status="FAILED",
            rows_read=0,
            rows_inserted=0,
            rows_failed=0,
        )
        raise

# --- CRUD (Sprint 2.2.2) ---

@router.put("/transactions/{id_economico}")
def update_transaction(id_economico: str, payload: TransactionUpdateRequest, current_user = Depends(require_admin)):
    """Atualiza transação real registrando audit_log."""
    updates = payload.dict(exclude_unset=True)
    if not repository.update_transaction(id_economico, updates, changed_by=current_user.username):
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    return {"message": "Transaction updated successfully"}

@router.put("/positions/{ticker}/{data_snapshot}")
def update_position(ticker: str, data_snapshot: str, payload: PositionUpdateRequest, current_user = Depends(require_admin)):
    """Atualiza posição real registrando audit_log."""
    updates = payload.dict(exclude_unset=True)
    if not repository.update_position(ticker, data_snapshot, updates, changed_by=current_user.username):
        raise HTTPException(status_code=404, detail="Posição não encontrada")
    return {"message": "Position updated successfully"}

@router.put("/dividends/{id_economico}")
def update_dividend(id_economico: str, payload: DividendUpdateRequest, current_user = Depends(require_admin)):
    """Atualiza dividendo real registrando audit_log."""
    updates = payload.dict(exclude_unset=True)
    if not repository.update_dividend(id_economico, updates, changed_by=current_user.username):
        raise HTTPException(status_code=404, detail="Dividendo não encontrado")
    return {"message": "Dividend updated successfully"}

@router.post("/categories/merge")
def merge_categories(payload: CategoryMergeRequest, current_user = Depends(require_admin)):
    """Merge de categorias real registrando audit_log."""
    affected = repository.merge_categories(payload.source_category, payload.target_category, changed_by=current_user.username)
    return {"message": "Categories merged successfully", "affected_rows": affected}

@router.post("/database/orphan-cleanup")
def detect_orphans(current_user = Depends(require_admin)):
    """Apenas detecta registros órfãos sem excluí-los (Sprint 2.2.3)."""
    return repository.get_orphans_count()

from app.api.schemas.governance import AdminPositionListResponse, AdminDividendListResponse, AdminCategoryListResponse

@router.get("/positions", response_model=AdminPositionListResponse)
def list_admin_positions(
    limit: int = 50,
    offset: int = 0,
    ticker: str = None,
    snapshot_date: str = None,
    classe_ativo: str = None,
    current_user = Depends(require_admin)
):
    items, total = queries.get_admin_positions(limit, offset, ticker, snapshot_date, classe_ativo)
    return AdminPositionListResponse(items=items, total=total, limit=limit, offset=offset)

@router.get("/dividends", response_model=AdminDividendListResponse)
def list_admin_dividends(
    limit: int = 50,
    offset: int = 0,
    ticker: str = None,
    start_date: str = None,
    end_date: str = None,
    tipo_evento: str = None,
    current_user = Depends(require_admin)
):
    items, total = queries.get_admin_dividends(limit, offset, ticker, start_date, end_date, tipo_evento)
    return AdminDividendListResponse(items=items, total=total, limit=limit, offset=offset)

@router.get("/categories", response_model=AdminCategoryListResponse)
def list_admin_categories(
    limit: int = 50,
    offset: int = 0,
    current_user = Depends(require_admin)
):
    items, total = queries.get_admin_categories(limit, offset)
    return AdminCategoryListResponse(items=items, total=total, limit=limit, offset=offset)