import pytest
from app.api.services.myprofit_parser import MyProfitParser
from app.api.services.pierre_parser import PierreParser

def test_myprofit_parser_proventos():
    csv_content = """Date,Operation,Ticker,Amount,Price
2026-06-01,BUY,AAPL,10,150.0
2026-06-02,SELL,GOOG,5,2800.0
"""
    parser = MyProfitParser()
    preview = parser.parse_preview(csv_content, "PROVENTOS")
    assert preview is not None

def test_myprofit_parser_posicoes():
    csv_content = """Ativo,Quantidade,Preço Médio,Cotação Atual
AAPL,10.0,150.0,160.0
GOOG,5.0,2800.0,2900.0
"""
    parser = MyProfitParser()
    preview = parser.parse_preview(csv_content, "POSICOES")
    assert preview is not None

def test_myprofit_parser_evolucao():
    csv_content = """Mês,Patrimônio,Rentabilidade da Carteira (%),Rentabilidade Acumulada (%)
2026-06,10000.0,5.0,10.0
"""
    parser = MyProfitParser()
    preview = parser.parse_preview(csv_content, "EVOLUCAO")
    assert preview is not None

def test_pierre_parser():
    txt_content = """n°,Data,Descrição,Categoria,Conta,Valor
1,01/06/2026,Compra de Ações AAPL,Investimentos,Banco,-1500,00
2,02/06/2026,Venda de Ações GOOG,Investimentos,Banco,14000,00"""
    parser = PierreParser()
    result = parser.parse(txt_content)
    assert result is not None
    assert len(result) == 2
