import hashlib
from typing import List
from backend.domains.imports.dto import CanonicalFinancialEvent, EventTypeEnum
from backend.domains.imports.parsers.nubank_fatura import NubankFaturaRowDTO

class NubankFaturaNormalizer:
    """Normalizer responsável por converter DTO intermediário no modelo Universal."""
    
    def normalize(self, rows: List[NubankFaturaRowDTO], raw_doc_id: str) -> List[CanonicalFinancialEvent]:
        events = []
        for row in rows:
            # Hash para uuid (faturas não trazem id único)
            unique_string = f"{row.data.isoformat()}-{row.titulo}-{row.valor}-{raw_doc_id}"
            ext_uuid = hashlib.md5(unique_string.encode('utf-8')).hexdigest()
            
            norm_desc = row.titulo
            if "Pagamento recebido" in norm_desc:
                norm_desc = "Pagamento de Fatura"
            
            events.append(CanonicalFinancialEvent(
                source_system="NUBANK",
                source_type="CSV_FATURA",
                event_type=EventTypeEnum.CREDIT_EXPENSE,
                transaction_date=row.data.date(),
                description=row.titulo,
                normalized_description=norm_desc,
                amount=row.valor,
                currency="BRL",
                credit_card="Nubank Geral",
                external_uuid=ext_uuid,
                raw_data={
                    "original_date": row.data.strftime("%Y-%m-%d"),
                    "original_amount": str(row.valor),
                    "title": row.titulo,
                    "raw_document_hash": raw_doc_id
                }
            ))
        return events
