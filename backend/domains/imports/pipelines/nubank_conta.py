from typing import Tuple, List
from backend.domains.imports.dto import RawDocument, CanonicalFinancialEvent
from backend.domains.imports.readers.nubank_conta import NubankContaReader
from backend.domains.imports.validators.nubank_conta import NubankContaValidator
from backend.domains.imports.parsers.nubank_conta import NubankContaParser
from backend.domains.imports.normalizers.nubank_conta import NubankContaNormalizer

class NubankContaPipeline:
    """Orquestra o pipeline exclusivo do Extrato de Conta Nubank."""
    
    def __init__(self):
        self.reader = NubankContaReader()
        self.validator = NubankContaValidator()
        self.parser = NubankContaParser()
        self.normalizer = NubankContaNormalizer()
        
    def execute(self, filepath: str) -> Tuple[RawDocument, List[CanonicalFinancialEvent]]:
        # 1. Leitura
        raw_doc = self.reader.read(filepath)
        
        # 2. Validação
        self.validator.validate(raw_doc)
        
        # 3. Parsing
        parsed_rows = self.parser.parse(raw_doc)
        
        # 4. Normalização
        canonical_events = self.normalizer.normalize(parsed_rows, raw_doc.document_hash)
        
        return raw_doc, canonical_events
