import hashlib
from typing import List
from backend.domains.imports.dto import CanonicalFinancialEvent, EventTypeEnum
from backend.domains.imports.parsers.pierre_txt import PierreTxtRowDTO

class PierreTxtNormalizer:
    """Normalizer responsável por converter DTO intermediário no modelo Universal."""
    
    def normalize(self, rows: List[PierreTxtRowDTO], raw_doc_id: str) -> List[CanonicalFinancialEvent]:
        events = []
        for i, row in enumerate(rows):
            # Hash para uuid, garantindo unicidade por linha dentro do arquivo
            unique_string = f"{row.data.isoformat()}-{row.descricao}-{row.valor}-{i}-{raw_doc_id}"
            ext_uuid = hashlib.md5(unique_string.encode('utf-8')).hexdigest()
            
            norm_desc = row.descricao
            if "Transferência enviada" in norm_desc:
                norm_desc = "Transferência Enviada"
            elif "Transferência Recebida" in norm_desc:
                norm_desc = "Transferência Recebida"
            
            events.append(CanonicalFinancialEvent(
                source_system="PIERRE",
                source_type="TXT",
                event_type=EventTypeEnum.CASH_FLOW,
                transaction_date=row.data.date(),
                description=f"{row.descricao} | {row.categoria}",
                normalized_description=norm_desc,
                amount=row.valor,
                currency="BRL",
                account=row.conta,
                external_uuid=ext_uuid,
                raw_data={
                    "original_date": row.data.strftime("%d/%m/%Y"),
                    "original_amount": str(row.valor),
                    "descricao": row.descricao,
                    "categoria": row.categoria,
                    "conta": row.conta,
                    "raw_document_hash": raw_doc_id
                }
            ))
        return events
