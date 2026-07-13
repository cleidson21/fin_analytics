import pytest
import os
import tempfile
import zipfile
import pandas as pd
from unittest.mock import patch, MagicMock
from backend.domains.investments.readers.b3_reader import B3CustodyReader, B3ReaderException

class TestB3CustodyReader:

    @pytest.fixture
    def reader(self):
        return B3CustodyReader()

    def test_file_not_found(self, reader):
        with pytest.raises(FileNotFoundError):
            reader.read("caminho_inexistente.csv")

    def test_invalid_zip_format(self, reader):
        # Cria um arquivo de texto normal, que não é um ZIP válido
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(b"Coluna1,Coluna2\n1,2")
            tmp_path = tmp.name

        try:
            with pytest.raises(B3ReaderException, match="não é um arquivo XLSX/ZIP válido"):
                reader.read(tmp_path)
        finally:
            os.remove(tmp_path)

    @patch("backend.domains.investments.readers.b3_reader.pd.ExcelFile")
    @patch("backend.domains.investments.readers.b3_reader.zipfile.is_zipfile", return_value=True)
    def test_read_mocked_sheets(self, mock_is_zip, mock_excel_file, reader):
        mock_excel = MagicMock()
        mock_excel.sheet_names = ["Posição - Ações", "Aba Desconhecida", "Posição - Fundos"]
        
        # Mock the parsing logic
        df_acoes = pd.DataFrame({"A": [1]})
        df_fundos = pd.DataFrame({"B": [2]})
        
        def mock_parse(sheet_name, **kwargs):
            if sheet_name == "Posição - Ações": return df_acoes
            if sheet_name == "Posição - Fundos": return df_fundos
            return pd.DataFrame()
            
        mock_excel.parse.side_effect = mock_parse
        mock_excel_file.return_value = mock_excel
        
        # Create a dummy file just to pass os.path.exists
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
            
        try:
            result = reader.read(tmp_path)
            
            # Deve carregar apenas as abas suportadas
            assert list(result.keys()) == ["Posição - Ações", "Posição - Fundos"]
            assert result["Posição - Ações"].equals(df_acoes)
            assert result["Posição - Fundos"].equals(df_fundos)
            # A "Aba Desconhecida" deve ter sido ignorada
            assert "Aba Desconhecida" not in result
        finally:
            os.remove(tmp_path)

    def test_functional_b3_sample(self, reader):
        """Teste funcional integrando com o arquivo de amostra real do projeto."""
        sample_path = os.path.join(
            os.path.dirname(__file__), 
            "..", "..", "..", "..", "samples", "Exemplo_Ativos_B3.csv"
        )
        # Normalizar caminho
        sample_path = os.path.normpath(sample_path)
        
        if not os.path.exists(sample_path):
            pytest.skip(f"Arquivo de amostra não encontrado: {sample_path}")
            
        result = reader.read(sample_path)
        
        assert isinstance(result, dict)
        assert len(result) > 0
        
        # O arquivo de exemplo deve ter as 4 abas mapeadas no B3_IMPORT_SPEC
        expected_sheets = [
            "Posição - Ações", 
            "Posição - Fundos", 
            "Posição - Tesouro Direto", 
            "Proventos Recebidos"
        ]
        
        for sheet in expected_sheets:
            assert sheet in result, f"Aba esperada ausente: {sheet}"
            df = result[sheet]
            assert not df.empty, f"O DataFrame da aba {sheet} está vazio"
            # O cabeçalho real começa na linha 0, então a coluna deve se chamar 'Produto'
            assert 'Produto' in df.columns, f"A coluna 'Produto' não foi encontrada no cabeçalho da aba {sheet}"
