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