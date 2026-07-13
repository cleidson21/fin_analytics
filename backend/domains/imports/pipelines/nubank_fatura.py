import logging
from typing import Tuple, List
from backend.domains.imports.dto import RawDocument, CanonicalFinancialEvent

logger = logging.getLogger(__name__)
from backend.domains.imports.readers.nubank_fatura import NubankFaturaReader
from backend.domains.imports.validators.nubank_fatura import NubankFaturaValidator
from backend.domains.imports.parsers.nubank_fatura import NubankFaturaParser
from backend.domains.imports.normalizers.nubank_fatura import NubankFaturaNormalizer

class NubankFaturaPipeline:
    """Orquestra o pipeline exclusivo do Extrato de Fatura Nubank."""
    
    def __init__(self):
        self.reader = NubankFaturaReader()
        self.validator = NubankFaturaValidator()
        self.parser = NubankFaturaParser()
        self.normalizer = NubankFaturaNormalizer()
        
    def execute(self, filepath: str) -> Tuple[RawDocument, List[CanonicalFinancialEvent]]:
        try:
            raw_doc = self.reader.read(filepath)
            self.validator.validate(raw_doc)
            parsed_rows = self.parser.parse(raw_doc)
            canonical_events = self.normalizer.normalize(parsed_rows, raw_doc.document_hash)
            return raw_doc, canonical_events
        except Exception as e:
            logger.error(f"Erro fatal no pipeline Nubank Fatura para o arquivo {filepath}: {e}")
            raise
