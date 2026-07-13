import hashlib
from typing import List
from backend.domains.imports.dto import CanonicalFinancialEvent, EventTypeEnum
from backend.domains.imports.parsers.myprofit_proventos import MyProfitProventosRowDTO

class MyProfitProventosNormalizer:
    """Normaliza DTOs de proventos do MyProfit para Eventos Canônicos."""
    
    def normalize(self, dtos: List[MyProfitProventosRowDTO], raw_doc_id: str) -> List[CanonicalFinancialEvent]:
        events = []
        
        for dto in dtos:
            # Gerando hash usando sha256
            canonical_seed = f"MYPROFIT_{dto.data_pgto.isoformat()}_{dto.recebido}_PROVENTO_{dto.ativo}".encode('utf-8')
            ext_hash = hashlib.sha256(canonical_seed).hexdigest()
            
            description = f"Provento Recebido - {dto.ativo}"
            
            event = CanonicalFinancialEvent(
                source_system="MYPROFIT",
                source_type="CSV_PROVENTOS",
                event_type=EventTypeEnum.DIVIDEND,
                transaction_date=dto.data_pgto,
                description=description,
                normalized_description=description,
                amount=dto.recebido,
                currency="BRL",
                asset=dto.ativo,
                quantity=dto.cotas,
                external_hash=ext_hash,
                raw_data={
                    "ativo": dto.ativo,
                    "recebido": str(dto.recebido),
                    "cotas": str(dto.cotas),
                    "raw_document_hash": raw_doc_id
                }
            )
            events.append(event)
            
        return events
