import pandas as pd
import hashlib
import logging
from typing import Dict, Any
from datetime import datetime, timezone
from backend.domains.imports.dto import RawDocument

logger = logging.getLogger(__name__)

class BaseCsvReader:
    """Classe base abstrata para leitura de arquivos CSV."""
    
    source_system = "BASE_CSV"
    
    def read(self, filepath: str) -> RawDocument:
        try:
            df = pd.read_csv(filepath, encoding='utf-8')
            encoding = 'utf-8'
        except UnicodeDecodeError:
            df = pd.read_csv(filepath, encoding='latin1')
            encoding = 'latin1'
        except Exception as e:
            logger.error(f"Erro ao ler CSV {filepath}: {e}")
            raise
            
        content_dict = df.to_dict(orient='records')
        doc_hash = hashlib.sha256(str(content_dict).encode('utf-8')).hexdigest()
        
        filename = filepath.replace("\\", "/").split("/")[-1]
        
        return RawDocument(
            source=self.source_system,
            filename=filename,
            mime_type="text/csv",
            encoding=encoding,
            parser_version="1.0.0",
            metadata={"total_lines": len(df)},
            content=content_dict,
            document_hash=doc_hash,
            created_at=datetime.now(timezone.utc)
        )
