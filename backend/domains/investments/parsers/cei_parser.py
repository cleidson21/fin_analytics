import logging
from typing import List, Optional
import pandas as pd
from decimal import Decimal
from backend.domains.investments.parsers.dto import RawB3Movement

logger = logging.getLogger(__name__)

class B3MovementsParserException(Exception):
    """Exceção base para erros durante o parsing de movimentações CEI da B3."""
    pass

class B3MovementsParser:
    """
    Parser especializado em converter DataFrames brutos da aba de Negociação da B3
    em uma lista de instâncias estritas (DTO Fraco) do tipo RawB3Movement.
    """
    
    REQUIRED_COLUMNS = [
        "Data do Negócio",
        "Tipo de Movimentação",
        "Instituição",
        "Código de Negociação",
        "Quantidade",
        "Preço",
        "Valor"
    ]

    OPTIONAL_COLUMNS = [
        "Mercado",
        "Prazo/Vencimento"
    ]
    
    def parse(self, df: pd.DataFrame) -> List[RawB3Movement]:
        """
        Padroniza colunas do DataFrame, aplica saneamento básico (como tratar hífens),
        e converte as linhas para RawB3Movement, validando a integridade estática.
        
        Args:
            df (pd.DataFrame): DataFrame contendo os dados brutos lidos pelo B3MovementsReader.
            
        Returns:
            List[RawB3Movement]: Lista de movimentações purificadas em nível DTO.
            
        Raises:
            B3MovementsParserException: Se a estrutura base for incompatível ou falhar.
        """
        if df is None:
            raise B3MovementsParserException("DataFrame recebido é None.")
            
        if df.empty:
            logger.warning("DataFrame vazio fornecido ao parser.")
            return []
            
        for col in self.REQUIRED_COLUMNS:
            if col not in df.columns:
                raise KeyError(f"Coluna obrigatória '{col}' ausente no arquivo da B3.")
                
        logger.info(f"Iniciando parse de {len(df)} linhas de movimentação B3.")
        
        parsed_movements: List[RawB3Movement] = []
        
        def clean_str(val):
            if pd.isna(val): return None
            val_str = str(val).strip()
            if val_str == "-" or val_str == "": return None
            return val_str

        def to_decimal(val):
            if pd.isna(val): return Decimal("0")
            return Decimal(str(val))

        def to_date_str(val):
            if pd.isna(val): return None
            if isinstance(val, pd.Timestamp) or hasattr(val, 'strftime'):
                return val.strftime("%d/%m/%Y")
            return str(val).strip()
            
        for _, row in df.iterrows():
            codigo = row.get("Código de Negociação")
            if pd.isna(codigo) or str(codigo).strip() == "" or str(codigo).strip() == "-":
                logger.warning("Linha ignorada: Código de Negociação ausente.")
                continue
                
            try:
                mov = RawB3Movement(
                    data_do_negocio=to_date_str(row.get("Data do Negócio")),
                    tipo_de_movimentacao=clean_str(row.get("Tipo de Movimentação")),
                    mercado=clean_str(row.get("Mercado")),
                    prazo_vencimento=clean_str(row.get("Prazo/Vencimento")),
                    instituicao=clean_str(row.get("Instituição")),
                    codigo_de_negociacao=clean_str(codigo),
                    quantidade=to_decimal(row.get("Quantidade")),
                    preco=to_decimal(row.get("Preço")),
                    valor=to_decimal(row.get("Valor"))
                )
                parsed_movements.append(mov)
            except Exception as e:
                logger.error(f"Falha de validação estrutural na linha: {str(e)}")
                raise
            
        logger.info(f"Parse concluído: {len(parsed_movements)} eventos brutos gerados.")
        return parsed_movements
