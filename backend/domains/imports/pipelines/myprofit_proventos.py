import logging
from typing import Tuple, List, Optional
from backend.domains.imports.dto import RawDocument, CanonicalFinancialEvent
from backend.domains.imports.readers.myprofit_csv import MyProfitProventosReader
from backend.domains.imports.validators.myprofit_proventos import MyProfitProventosValidator
from backend.domains.imports.parsers.myprofit_proventos import MyProfitProventosParser
from backend.domains.imports.normalizers.myprofit_proventos import MyProfitProventosNormalizer

logger = logging.getLogger(__name__)

class MyProfitProventosPipeline:
    """Orquestrador completo para importação de proventos do MyProfit."""
    
    def __init__(self):
        self.reader = MyProfitProventosReader()
        self.validator = MyProfitProventosValidator()
        self.parser = MyProfitProventosParser()
        self.normalizer = MyProfitProventosNormalizer()
        
    def execute(self, filepath: str) -> Tuple[bool, Optional[RawDocument], List[CanonicalFinancialEvent]]:
        try:
            logger.info(f"Iniciando pipeline MyProfit Proventos para o arquivo: {filepath}")
            
            raw_doc = self.reader.read(filepath)
            
            is_valid = self.validator.validate(raw_doc)
            if not is_valid:
                logger.warning(f"Arquivo {filepath} falhou na validação estrutural do MyProfit Proventos.")
                return False, raw_doc, []
                
            parsed_rows = self.parser.parse(raw_doc)
            
            canonical_events = self.normalizer.normalize(parsed_rows, raw_doc_id=raw_doc.document_hash)
            
            logger.info(f"Pipeline concluído. {len(canonical_events)} eventos extraídos.")
            return True, raw_doc, canonical_events
            
        except Exception as e:
            logger.error(f"Falha catastrófica no pipeline MyProfit Proventos para {filepath}: {e}")
            # Retornando vazio conforme padrão defensivo da EA3
            return False, None, []
