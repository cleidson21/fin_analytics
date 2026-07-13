from typing import List, Dict, Any
from backend.domains.imports.dto import RawDocument

class MyProfitProventosValidator:
    """Validador estrutural do CSV de Proventos do MyProfit."""
    
    REQUIRED_COLUMNS = ["Ativo", "Recebido", "Data pgto.", "Cotas"]
    
    def validate(self, doc: RawDocument) -> bool:
        if not doc or not doc.content:
            return False
            
        if not isinstance(doc.content, list):
            return False
            
        if len(doc.content) == 0:
            return False
            
        first_row = doc.content[0]
        
        for col in self.REQUIRED_COLUMNS:
            if col not in first_row:
                return False
                
        return True
