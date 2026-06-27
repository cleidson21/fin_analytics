from backend.domains.imports.dto import RawDocument

class NubankFaturaValidator:
    """Validator do RawDocument extraído da Fatura Nubank."""
    
    def validate(self, doc: RawDocument) -> None:
        if doc.source != "NUBANK_FATURA_CSV":
            raise ValueError(f"Validator incompatível com source: {doc.source}")
        
        content = doc.content
        if not content or not isinstance(content, list):
            raise ValueError("Documento está vazio ou não é uma lista de registros.")
            
        required_cols = {"date", "title", "amount"}
        first_row = content[0]
        missing = required_cols - set(first_row.keys())
        if missing:
            raise ValueError(f"Colunas obrigatórias ausentes: {missing}")
            
        for i, row in enumerate(content):
            date_str = str(row.get("date", ""))
            if len(date_str.split("-")) != 3:
                raise ValueError(f"Formato de data inválido na linha {i+1}: {date_str}")
                
            amount_str = str(row.get("amount", ""))
            if not amount_str:
                raise ValueError(f"Valor numérico vazio na linha {i+1}")
