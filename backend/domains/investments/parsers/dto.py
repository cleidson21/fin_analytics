from typing import Optional
from decimal import Decimal
from pydantic import BaseModel

class RawB3StockPosition(BaseModel):
    produto: Optional[str] = None
    instituicao: Optional[str] = None
    conta: Optional[str] = None
    codigo_negociacao: str
    cnpj_empresa: Optional[str] = None
    codigo_isin: Optional[str] = None
    tipo: Optional[str] = None
    escriturador: Optional[str] = None
    quantidade: Decimal
    quantidade_disponivel: Optional[Decimal] = None
    quantidade_indisponivel: Optional[Decimal] = None
    motivo: Optional[str] = None
    preco_fechamento: Optional[Decimal] = None
    valor_atualizado: Optional[Decimal] = None

class RawB3FundPosition(BaseModel):
    produto: Optional[str] = None
    instituicao: Optional[str] = None
    conta: Optional[str] = None
    codigo_negociacao: str
    cnpj_fundo: Optional[str] = None
    codigo_isin: Optional[str] = None
    tipo: Optional[str] = None
    administrador: Optional[str] = None
    quantidade: Decimal
    quantidade_disponivel: Optional[Decimal] = None
    quantidade_indisponivel: Optional[Decimal] = None
    motivo: Optional[str] = None
    preco_fechamento: Optional[Decimal] = None
    valor_atualizado: Optional[Decimal] = None

class RawB3TreasuryPosition(BaseModel):
    produto: Optional[str] = None
    instituicao: Optional[str] = None
    codigo_isin: str
    indexador: Optional[str] = None
    vencimento: Optional[str] = None
    quantidade: Decimal
    quantidade_disponivel: Optional[Decimal] = None
    quantidade_indisponivel: Optional[Decimal] = None
    motivo: Optional[str] = None
    valor_aplicado: Optional[Decimal] = None
    valor_bruto: Optional[Decimal] = None
    valor_liquido: Optional[Decimal] = None
    valor_atualizado: Optional[Decimal] = None

class RawB3Dividend(BaseModel):
    produto: str
    pagamento: Optional[str]
    tipo_evento: Optional[str]
    instituicao: Optional[str]
    quantidade: Optional[Decimal] = None
    preco_unitario: Optional[Decimal] = None
    valor_liquido: Optional[Decimal] = None

class RawB3Movement(BaseModel):
    """
    Representa uma linha bruta lida do arquivo de Negociação da B3.
    """
    data_do_negocio: str
    tipo_de_movimentacao: str
    mercado: Optional[str] = None
    prazo_vencimento: Optional[str] = None
    instituicao: str
    codigo_de_negociacao: str
    quantidade: Decimal
    preco: Decimal
    valor: Decimal
