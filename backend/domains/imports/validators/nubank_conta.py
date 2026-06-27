from backend.domains.imports.dto import RawDocument

class NubankContaValidator:
    """Validator do RawDocument extraído do Nubank Conta."""
    
    def validate(self, doc: RawDocument) -> None:
        if doc.source != "NUBANK_CONTA_CSV":
            raise ValueError(f"Validator incompatível com source: {doc.source}")
        
        content = doc.content
        if not content or not isinstance(content, list):
            raise ValueError("Documento está vazio ou não é uma lista de registros.")
            
        required_cols = {"Data", "Valor", "Identificador", "Descrição"}
        first_row = content[0]
        missing = required_cols - set(first_row.keys())
        if missing:
            raise ValueError(f"Colunas obrigatórias ausentes: {missing}")
            
        for i, row in enumerate(content):
            date_str = str(row.get("Data", ""))
            if len(date_str.split("/")) != 3:
                raise ValueError(f"Formato de data inválido na linha {i+1}: {date_str}")
                
            try:
                float(row.get("Valor", ""))
            except ValueError:
                raise ValueError(f"Valor numérico inválido na linha {i+1}")
