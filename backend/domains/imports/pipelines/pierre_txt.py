from typing import List, Tuple
from backend.domains.imports.dto import RawDocument, CanonicalFinancialEvent
from backend.domains.imports.readers.pierre_txt import PierreTxtReader
from backend.domains.imports.validators.pierre_txt import PierreTxtValidator
from backend.domains.imports.parsers.pierre_txt import PierreTxtParser
from backend.domains.imports.normalizers.pierre_txt import PierreTxtNormalizer

class PierreTxtPipeline:
    """Orquestrador do processo de importação do arquivo TXT do Pierre."""
    
    def __init__(self):
        self.reader = PierreTxtReader()
        self.validator = PierreTxtValidator()
        self.parser = PierreTxtParser()
        self.normalizer = PierreTxtNormalizer()
        
    def execute(self, filepath: str) -> Tuple[RawDocument, List[CanonicalFinancialEvent]]:
        # 1. Leitura
        raw_doc = self.reader.read(filepath)
        
        # 2. Validação
        self.validator.validate(raw_doc)
        
        # 3. Parsing
        parsed_rows = self.parser.parse(raw_doc)
        
        # 4. Normalização
        canonical_events = self.normalizer.normalize(
            rows=parsed_rows,
            raw_doc_id=raw_doc.document_hash
        )
        
        return raw_doc, canonical_events
