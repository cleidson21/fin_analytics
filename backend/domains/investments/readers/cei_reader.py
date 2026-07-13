import os
import zipfile
import logging
import pandas as pd

logger = logging.getLogger(__name__)

class B3MovementsReaderException(Exception):
    """Exceção base para erros durante a leitura de arquivos de movimentação CEI da B3."""
    pass

class B3MovementsReader:
    """
    Reader especializado em arquivos de Negociação (Movimentações) da B3.
    """
    
    TARGET_SHEET = "Negociação"
    
    def read(self, file_path: str) -> pd.DataFrame:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
        if not zipfile.is_zipfile(file_path):
            raise ValueError(f"O arquivo {file_path} não é um arquivo XLSX/ZIP válido.")
            
        try:
            excel_file = pd.ExcelFile(file_path, engine="openpyxl")
            sheets = excel_file.sheet_names
            
            if self.TARGET_SHEET not in sheets:
                raise ValueError(f"Aba obrigatória '{self.TARGET_SHEET}' não encontrada no arquivo.")
                
            logger.info(f"Lendo aba reconhecida: {self.TARGET_SHEET}")
            df = excel_file.parse(self.TARGET_SHEET, header=0)
            
            return df
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Erro ao ler arquivo de negociação B3: {str(e)}")
            raise B3MovementsReaderException(f"Falha na extração de dados B3: {str(e)}") from e
