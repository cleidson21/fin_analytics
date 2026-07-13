import pytest
import os
import pandas as pd
from decimal import Decimal
from backend.domains.investments.parsers.b3_parser import B3CustodyParser, B3ParserException
from backend.domains.investments.readers.b3_reader import B3CustodyReader

class TestB3CustodyParser:
    
    @pytest.fixture
    def parser(self):
        return B3CustodyParser()
        
    def test_parse_acoes(self, parser):
        df = pd.DataFrame({
            "Produto": ["Ação X", None, "Total"],
            "Instituição": ["Corretora A", None, None],
            "Conta": ["123", None, None],
            "Código de Negociação": ["TICK3", None, None],
            "CNPJ da Empresa": ["12345678000100", None, None],
            "Código ISIN / Distribuição": ["BRTICKACNOR", None, None],
            "Tipo": ["ON", None, None],
            "Escriturador": ["Banco A", None, None],
            "Quantidade": ["100", None, None],
            "Quantidade Disponível": ["100", None, None],
            "Quantidade Indisponível": ["-", None, None],
            "Motivo": ["-", None, None],
            "Preço de Fechamento": ["10.50", None, None],
            "Valor Atualizado": ["1050.00", None, "1050.00"]
        })
        
        result = parser.parse({"Posição - Ações": df})
        acoes = result["Posição - Ações"]
        
        # Apenas 1 linha válida deve ser retornada (linha Total e None ignoradas)
        assert len(acoes) == 1
        acao = acoes[0]
        
        assert acao.codigo_negociacao == "TICK3"
        assert acao.quantidade == Decimal("100")
        assert acao.quantidade_indisponivel is None  # O '-' virou None
        assert acao.preco_fechamento == Decimal("10.50")
        assert acao.motivo is None

    def test_parse_fundos(self, parser):
        df = pd.DataFrame({
            "Produto": ["Fundo Y"],
            "Instituição": ["Corretora B"],
            "Conta": ["321"],
            "Código de Negociação": ["FUND11"],
            "CNPJ do Fundo": ["00000000000100"],
            "Código ISIN / Distribuição": ["BRFUNDCTF"],
            "Tipo": ["Cotas"],
            "Administrador": ["Banco B"],
            "Quantidade": ["50"],
            "Quantidade Disponível": ["50"],
            "Quantidade Indisponível": ["0"],
            "Motivo": [""],
            "Preço de Fechamento": ["100.00"],
            "Valor Atualizado": ["5000.00"]
        })
        
        result = parser.parse({"Posição - Fundos": df})
        fundos = result["Posição - Fundos"]
        
        assert len(fundos) == 1
        assert fundos[0].codigo_negociacao == "FUND11"
        assert fundos[0].quantidade == Decimal("50")
        assert fundos[0].motivo is None

    def test_parse_tesouro(self, parser):
        df = pd.DataFrame({
            "Produto": ["Tesouro IPCA"],
            "Instituição": ["Corretora C"],
            "Código ISIN": ["BRSTNCNTB0O7"],
            "Indexador": ["IPCA"],
            "Vencimento": ["15/05/2035"],
            "Quantidade": ["0.73"],
            "Quantidade Disponível": ["0.73"],
            "Quantidade Indisponível": ["0"],
            "Motivo": ["-"],
            "Valor Aplicado": ["3073.34"],
            "Valor bruto": ["3087.13"],
            "Valor líquido": ["3084.49"],
            "Valor Atualizado": ["3087.13"]
        })
        
        result = parser.parse({"Posição - Tesouro Direto": df})
        tesouro = result["Posição - Tesouro Direto"]
        
        assert len(tesouro) == 1
        assert tesouro[0].codigo_isin == "BRSTNCNTB0O7"
        assert tesouro[0].quantidade == Decimal("0.73")
        assert tesouro[0].valor_bruto == Decimal("3087.13")

    def test_parse_proventos(self, parser):
        df = pd.DataFrame({
            "Produto": ["TICK3 - TICKER S/A"],
            "Pagamento": ["27/05/2026"],
            "Tipo de Evento": ["Dividendo"],
            "Instituição": ["Corretora D"],
            "Quantidade": ["100"],
            "Preço unitário": ["0.15"],
            "Valor líquido": ["15.00"]
        })
        
        result = parser.parse({"Proventos Recebidos": df})
        provento = result["Proventos Recebidos"]
        
        assert len(provento) == 1
        assert provento[0].produto == "TICK3 - TICKER S/A"
        assert provento[0].quantidade == Decimal("100")
        assert provento[0].valor_liquido == Decimal("15.00")

    def test_missing_required_column(self, parser):
        # Ações exige 'Código de Negociação' para o dropna
        df = pd.DataFrame({
            "Produto": ["Ação X"],
            # Faltando Código de Negociação
            "Quantidade": ["100"]
        })
        
        with pytest.raises(B3ParserException, match="ausente"):
            parser.parse({"Posição - Ações": df})

    def test_invalid_numeric(self, parser):
        df = pd.DataFrame({
            "Código de Negociação": ["TICK3"],
            "Quantidade": ["abc"] # Inválido
        })
        
        with pytest.raises(B3ParserException, match="Valor numérico inválido"):
            parser.parse({"Posição - Ações": df})

    def test_functional_integration(self, parser):
        """Teste de integração unindo o Reader B3 e o Parser B3 usando amostra real."""
        sample_path = os.path.join(
            os.path.dirname(__file__), 
            "..", "..", "..", "..", "samples", "Exemplo_Ativos_B3.csv"
        )
        sample_path = os.path.normpath(sample_path)
        
        if not os.path.exists(sample_path):
            pytest.skip(f"Amostra não encontrada em {sample_path}")
            
        reader = B3CustodyReader()
        dataframes = reader.read(sample_path)
        
        # O reader carrega perfeitamente. Agora o parser:
        parsed_data = parser.parse(dataframes)
        
        # Validando resultados gerais
        assert "Posição - Ações" in parsed_data
        assert "Posição - Tesouro Direto" in parsed_data
        
        acoes = parsed_data["Posição - Ações"]
        assert len(acoes) > 0
        assert hasattr(acoes[0], "codigo_negociacao")
        assert isinstance(acoes[0].quantidade, Decimal)
        
        tesouro = parsed_data["Posição - Tesouro Direto"]
        assert len(tesouro) > 0
        assert hasattr(tesouro[0], "codigo_isin")
        assert isinstance(tesouro[0].quantidade, Decimal)
