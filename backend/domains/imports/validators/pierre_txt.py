import re
from backend.domains.imports.dto import RawDocument

class PierreTxtValidator:
    """Validator do RawDocument extraído do Pierre TXT."""
    
    def validate(self, doc: RawDocument) -> None:
        if doc.source != "PIERRE_TXT":
            raise ValueError(f"Validator incompatível com source: {doc.source}")
        
        content = doc.content
        if not content or not isinstance(content, list):
            raise ValueError("Documento está vazio ou não é uma lista de linhas.")
            
        # Verificar se tem pelo menos uma linha de transação válida
        has_transaction = False
        for i, line in enumerate(content):
            if re.match(r'^(\d{2}/\d{2}/\d{4})\s+(.+)$', line):
                has_transaction = True
                break
                
        if not has_transaction:
            raise ValueError("Nenhuma transação válida encontrada no arquivo TXT.")
