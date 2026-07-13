import os
import zipfile
import logging
from typing import Dict
import pandas as pd

logger = logging.getLogger(__name__)

class B3ReaderException(Exception):
    """Exceção base para erros durante a leitura de arquivos da B3."""
    pass

class B3CustodyReader:
    """
    Reader especializado em arquivos da Área do Investidor (B3).
    Apesar da extensão ser comumente reportada como .csv, o arquivo real é um XLSX (Zip archive).
    
    Responsabilidade Exclusiva:
    - Identificar o formato real do arquivo.
    - Carregar as planilhas existentes utilizando openpyxl.
    - Retornar um dicionário de DataFrames estruturado por aba.
    """
    
    SUPPORTED_SHEETS = [
        "Posição - Ações",
        "Posição - Fundos",
        "Posição - Tesouro Direto",
        "Proventos Recebidos"
    ]
    
    def read(self, file_path: str) -> Dict[str, pd.DataFrame]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
        # Tratamento de robustez: verificar se é um ZIP válido (XLSX) 
        # para não depender da extensão nominal ".csv" e evitar crashes no pandas
        if not zipfile.is_zipfile(file_path):
            raise B3ReaderException(f"O arquivo {file_path} não é um arquivo XLSX/ZIP válido.")
            
        try:
            # Descoberta dinâmica de planilhas
            excel_file = pd.ExcelFile(file_path, engine="openpyxl")
            sheets = excel_file.sheet_names
            
            result = {}
            for sheet in sheets:
                if sheet in self.SUPPORTED_SHEETS:
                    logger.info(f"Lendo aba reconhecida: {sheet}")
                    # Lê a aba inteira. Cabeçalho esperado na linha 0.
                    df = excel_file.parse(sheet, header=0)
                    result[sheet] = df
                else:
                    logger.warning(f"Aba desconhecida ignorada pelo Reader B3: {sheet}")
            
            if not result:
                raise B3ReaderException("Nenhuma aba suportada foi encontrada no arquivo.")
                
            return result
            
        except Exception as e:
            logger.error(f"Erro ao ler arquivo B3: {str(e)}")
            raise B3ReaderException(f"Falha na extração de dados B3: {str(e)}") from e
