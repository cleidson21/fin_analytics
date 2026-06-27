from typing import List
from backend.domains.imports.dto import CanonicalFinancialEvent, EventTypeEnum
from backend.domains.imports.parsers.nubank_conta import NubankContaRowDTO

class NubankContaNormalizer:
    """Normalizer responsável por converter DTO intermediário no modelo Universal."""
    
    def normalize(self, rows: List[NubankContaRowDTO], raw_doc_id: str) -> List[CanonicalFinancialEvent]:
        events = []
        for row in rows:
            ext_uuid = row.identificador
            
            # Heurística mínima descritiva
            norm_desc = row.descricao
            if "Transferência recebida pelo Pix" in norm_desc:
                norm_desc = "Pix Recebido"
            elif "Transferência enviada pelo Pix" in norm_desc:
                norm_desc = "Pix Enviado"
            elif "Transferência de saldo NuInvest" in norm_desc:
                norm_desc = "Transferência NuInvest"
            elif "Aplicação RDB" in norm_desc:
                norm_desc = "Aplicação RDB"
            elif "Resgate RDB" in norm_desc:
                norm_desc = "Resgate RDB"
            
            events.append(CanonicalFinancialEvent(
                source_system="NUBANK",
                source_type="CSV_CONTA",
                event_type=EventTypeEnum.CASH_FLOW,
                transaction_date=row.data.date(),
                description=row.descricao,
                normalized_description=norm_desc,
                amount=row.valor,
                currency="BRL",
                external_uuid=ext_uuid,
                raw_data={
                    "original_date": row.data.strftime("%d/%m/%Y"),
                    "original_amount": str(row.valor),
                    "identificador": row.identificador,
                    "descricao": row.descricao,
                    "raw_document_hash": raw_doc_id
                }
            ))
        return events
