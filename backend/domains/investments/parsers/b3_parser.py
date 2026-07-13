import pandas as pd
from typing import Dict, List, Any, Optional
from decimal import Decimal
from backend.domains.investments.parsers.dto import (
    RawB3StockPosition, RawB3FundPosition, RawB3TreasuryPosition, RawB3Dividend
)

class B3ParserException(Exception):
    pass

class B3CustodyParser:
    """
    Parser responsável por transformar os DataFrames brutos da B3 em 
    DTOs intermediários fortemente tipados.
    Nenhuma regra de negócio ou reconciliação é aplicada aqui.
    """
    
    def parse(self, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, List[Any]]:
        result = {}
        for sheet_name, df in dataframes.items():
            if df.empty:
                result[sheet_name] = []
                continue
                
            try:
                if sheet_name == "Posição - Ações":
                    result[sheet_name] = self._parse_acoes(df)
                elif sheet_name == "Posição - Fundos":
                    result[sheet_name] = self._parse_fundos(df)
                elif sheet_name == "Posição - Tesouro Direto":
                    result[sheet_name] = self._parse_tesouro(df)
                elif sheet_name == "Proventos Recebidos":
                    result[sheet_name] = self._parse_proventos(df)
                else:
                    result[sheet_name] = []
            except KeyError as e:
                raise B3ParserException(f"Coluna obrigatória ausente na aba '{sheet_name}': {e}")
            except Exception as e:
                raise B3ParserException(f"Erro ao processar aba '{sheet_name}': {e}")
                
        return result

    def _clean_decimal(self, value) -> Optional[Decimal]:
        if pd.isna(value):
            return None
        s = str(value).strip()
        if s == "-" or s == "":
            return None
        # Se for uma string com vírgula, tratamos como padrão brasileiro
        if isinstance(value, str) and "," in value:
            s = s.replace(".", "").replace(",", ".")
        try:
            return Decimal(str(s))
        except:
            raise B3ParserException(f"Valor numérico inválido: {value}")
            
    def _clean_str(self, value) -> Optional[str]:
        if pd.isna(value):
            return None
        s = str(value).strip()
        return None if s == "-" or s == "" else s

    def _parse_acoes(self, df: pd.DataFrame) -> List[RawB3StockPosition]:
        # Drop rows where 'Código de Negociação' is NaN (removes footer/Totals)
        df_clean = df.dropna(subset=['Código de Negociação'])
        parsed = []
        for _, row in df_clean.iterrows():
            parsed.append(RawB3StockPosition(
                produto=self._clean_str(row.get('Produto')),
                instituicao=self._clean_str(row.get('Instituição')),
                conta=self._clean_str(row.get('Conta')),
                codigo_negociacao=self._clean_str(row['Código de Negociação']),
                cnpj_empresa=self._clean_str(row.get('CNPJ da Empresa')),
                codigo_isin=self._clean_str(row.get('Código ISIN / Distribuição')),
                tipo=self._clean_str(row.get('Tipo')),
                escriturador=self._clean_str(row.get('Escriturador')),
                quantidade=self._clean_decimal(row['Quantidade']) or Decimal('0'),
                quantidade_disponivel=self._clean_decimal(row.get('Quantidade Disponível')),
                quantidade_indisponivel=self._clean_decimal(row.get('Quantidade Indisponível')),
                motivo=self._clean_str(row.get('Motivo')),
                preco_fechamento=self._clean_decimal(row.get('Preço de Fechamento')),
                valor_atualizado=self._clean_decimal(row.get('Valor Atualizado'))
            ))
        return parsed

    def _parse_fundos(self, df: pd.DataFrame) -> List[RawB3FundPosition]:
        df_clean = df.dropna(subset=['Código de Negociação'])
        parsed = []
        for _, row in df_clean.iterrows():
            parsed.append(RawB3FundPosition(
                produto=self._clean_str(row.get('Produto')),
                instituicao=self._clean_str(row.get('Instituição')),
                conta=self._clean_str(row.get('Conta')),
                codigo_negociacao=self._clean_str(row['Código de Negociação']),
                cnpj_fundo=self._clean_str(row.get('CNPJ do Fundo')),
                codigo_isin=self._clean_str(row.get('Código ISIN / Distribuição')),
                tipo=self._clean_str(row.get('Tipo')),
                administrador=self._clean_str(row.get('Administrador')),
                quantidade=self._clean_decimal(row['Quantidade']) or Decimal('0'),
                quantidade_disponivel=self._clean_decimal(row.get('Quantidade Disponível')),
                quantidade_indisponivel=self._clean_decimal(row.get('Quantidade Indisponível')),
                motivo=self._clean_str(row.get('Motivo')),
                preco_fechamento=self._clean_decimal(row.get('Preço de Fechamento')),
                valor_atualizado=self._clean_decimal(row.get('Valor Atualizado'))
            ))
        return parsed

    def _parse_tesouro(self, df: pd.DataFrame) -> List[RawB3TreasuryPosition]:
        df_clean = df.dropna(subset=['Código ISIN'])
        parsed = []
        for _, row in df_clean.iterrows():
            parsed.append(RawB3TreasuryPosition(
                produto=self._clean_str(row.get('Produto')),
                instituicao=self._clean_str(row.get('Instituição')),
                codigo_isin=self._clean_str(row['Código ISIN']),
                indexador=self._clean_str(row.get('Indexador')),
                vencimento=self._clean_str(row.get('Vencimento')),
                quantidade=self._clean_decimal(row['Quantidade']) or Decimal('0'),
                quantidade_disponivel=self._clean_decimal(row.get('Quantidade Disponível')),
                quantidade_indisponivel=self._clean_decimal(row.get('Quantidade Indisponível')),
                motivo=self._clean_str(row.get('Motivo')),
                valor_aplicado=self._clean_decimal(row.get('Valor Aplicado')),
                valor_bruto=self._clean_decimal(row.get('Valor bruto')),
                valor_liquido=self._clean_decimal(row.get('Valor líquido')),
                valor_atualizado=self._clean_decimal(row.get('Valor Atualizado'))
            ))
        return parsed

    def _parse_proventos(self, df: pd.DataFrame) -> List[RawB3Dividend]:
        df_clean = df.dropna(subset=['Produto'])
        parsed = []
        for _, row in df_clean.iterrows():
            parsed.append(RawB3Dividend(
                produto=self._clean_str(row['Produto']),
                pagamento=self._clean_str(row.get('Pagamento')),
                tipo_evento=self._clean_str(row.get('Tipo de Evento')),
                instituicao=self._clean_str(row.get('Instituição')),
                quantidade=self._clean_decimal(row.get('Quantidade')),
                preco_unitario=self._clean_decimal(row.get('Preço unitário')),
                valor_liquido=self._clean_decimal(row.get('Valor líquido'))
            ))
        return parsed
