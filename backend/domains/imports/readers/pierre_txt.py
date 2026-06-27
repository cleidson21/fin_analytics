import hashlib
from typing import List
from datetime import datetime, timezone
from backend.domains.imports.dto import RawDocument

class PierreTxtReader:
    """Reader responsável por extrair dados do arquivo TXT do Pierre."""
    
    def read(self, filepath: str) -> RawDocument:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            encoding = 'utf-8'
        except UnicodeDecodeError:
            with open(filepath, 'r', encoding='latin1') as f:
                lines = f.readlines()
            encoding = 'latin1'
            
        content_lines = [line.rstrip() for line in lines]
        doc_hash = hashlib.sha256(str(content_lines).encode('utf-8')).hexdigest()
        
        filename = filepath.replace("\\", "/").split("/")[-1]
        
        return RawDocument(
            source="PIERRE_TXT",
            filename=filename,
            mime_type="text/plain",
            encoding=encoding,
            parser_version="1.0.0",
            metadata={"total_lines": len(content_lines)},
            content=content_lines,
            document_hash=doc_hash,
            created_at=datetime.now(timezone.utc)
        )
