from decimal import Decimal

from pydantic import BaseModel


class PierreImportRequest(BaseModel):
    raw_text: str


class PierreImportPreviewItem(BaseModel):
    date: str
    description: str
    amount: Decimal
    status: str


class PierreImportPreview(BaseModel):
    items: list[PierreImportPreviewItem]


class PierreImportResponse(BaseModel):
    run_id: str
    preview: PierreImportPreview

class MyProfitImportRequest(BaseModel):
    raw_text: str
    file_name: str

class MyProfitPreview(BaseModel):
    source_type: str
    detected_file_type: str
    total_rows: int
    period_start: str | None
    period_end: str | None
    tickers_found: list[str]
    warnings: int
    errors: int

class MyProfitImportResponse(BaseModel):
    run_id: str
    preview: MyProfitPreview


class QuarantineTransaction(BaseModel):
    data: str
    descricao_original: str
    valor: Decimal
    identificador_externo: str | None


class ImportStatusItem(BaseModel):
    source_line_no: int
    description: str


class ImportStatusResponse(BaseModel):
    last_items: list[ImportStatusItem]
    next_line: int


class ImportRunItem(BaseModel):
    id: str
    source_type: str
    file_name: str
    checksum: str
    started_at: str
    finished_at: str | None
    status: str
    rows_read: int
    rows_inserted: int
    rows_updated: int
    rows_failed: int
    created_by: str | None


class ImportRunListResponse(BaseModel):
    items: list[ImportRunItem]
    total: int

class DashboardMetricsResponse(BaseModel):
    total_runs: int
    confirmed_runs: int
    pending_runs: int
    lines_inserted: int
    lines_updated: int
    lines_failed: int
    last_import: str | None
class AdminPositionItem(BaseModel):
    ticker: str
    snapshot_date: str
    quantidade: Decimal
    preco_medio: Decimal
    valor_total: Decimal
    classe_ativo: str | None
    observacao: str | None

class AdminPositionListResponse(BaseModel):
    items: list[AdminPositionItem]
    total: int
    limit: int
    offset: int

class AdminDividendItem(BaseModel):
    id_economico: str
    ticker: str
    tipo_evento: str | None
    valor: Decimal
    data_pagamento: str
    observacao: str | None

class AdminDividendListResponse(BaseModel):
    items: list[AdminDividendItem]
    total: int
    limit: int
    offset: int

class AdminCategoryItem(BaseModel):
    categoria: str
    quantidade_transacoes: int

class AdminCategoryListResponse(BaseModel):
    items: list[AdminCategoryItem]
    total: int
    limit: int
    offset: int

