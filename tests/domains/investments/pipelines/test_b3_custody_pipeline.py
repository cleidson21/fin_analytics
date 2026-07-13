import pytest
import os
from datetime import date
from unittest.mock import patch, MagicMock
from backend.domains.investments.pipelines.b3_custody_pipeline import B3CustodyPipeline, PipelineResult
from backend.domains.investments.readers.b3_reader import B3ReaderException
from backend.domains.investments.parsers.b3_parser import B3ParserException

class TestB3CustodyPipeline:
    
    @pytest.fixture
    def pipeline(self):
        return B3CustodyPipeline()
        
    @pytest.fixture
    def ref_date(self):
        return date(2026, 7, 3)

    def test_file_not_found(self, pipeline, ref_date):
        result = pipeline.execute("caminho_fake.csv", ref_date)
        
        assert result.status == "FAILED"
        assert len(result.errors) > 0
        assert "não encontrado" in result.errors[0].lower()
        assert result.processed_count == 0

    @patch("backend.domains.investments.pipelines.b3_custody_pipeline.B3CustodyReader")
    def test_reader_error(self, mock_reader_cls, ref_date):
        mock_reader = MagicMock()
        mock_reader.read.side_effect = B3ReaderException("Formato inválido")
        pipeline = B3CustodyPipeline(reader=mock_reader)
        
        result = pipeline.execute("dummy.xlsx", ref_date)
        
        assert result.status == "FAILED"
        assert len(result.errors) == 1
        assert "Formato inválido" in result.errors[0]
        assert result.processed_count == 0

    @patch("backend.domains.investments.pipelines.b3_custody_pipeline.B3CustodyReader")
    @patch("backend.domains.investments.pipelines.b3_custody_pipeline.B3CustodyParser")
    def test_parser_error(self, mock_parser_cls, mock_reader_cls, ref_date):
        mock_reader = MagicMock()
        mock_reader.read.return_value = {"Posição - Ações": MagicMock()}
        
        mock_parser = MagicMock()
        mock_parser.parse.side_effect = B3ParserException("Coluna ausente")
        
        pipeline = B3CustodyPipeline(reader=mock_reader, parser=mock_parser)
        
        result = pipeline.execute("dummy.xlsx", ref_date)
        
        assert result.status == "FAILED"
        assert len(result.errors) == 1
        assert "Coluna ausente" in result.errors[0]

    @patch("backend.domains.investments.pipelines.b3_custody_pipeline.B3CustodyReader")
    @patch("backend.domains.investments.pipelines.b3_custody_pipeline.B3CustodyParser")
    @patch("backend.domains.investments.pipelines.b3_custody_pipeline.B3CustodyNormalizer")
    def test_normalizer_error(self, mock_normalizer_cls, mock_parser_cls, mock_reader_cls, ref_date):
        mock_reader = MagicMock()
        mock_reader.read.return_value = {"Posição - Ações": MagicMock()}
        
        # Simula raw_dto de ação
        dummy_raw = MagicMock()
        dummy_raw.codigo_negociacao = "TICK3"
        mock_parser = MagicMock()
        mock_parser.parse.return_value = {"Posição - Ações": [dummy_raw]}
        
        # Simula erro de normalização para UM dos registros
        mock_normalizer = MagicMock()
        mock_normalizer.normalize_stock.side_effect = Exception("Erro maluco")
        
        pipeline = B3CustodyPipeline(reader=mock_reader, parser=mock_parser, normalizer=mock_normalizer)
        result = pipeline.execute("dummy.xlsx", ref_date)
        
        assert result.status == "FAILED" # Só tinha 1 item e falhou
        assert result.discarded_count == 1
        assert result.processed_count == 0
        assert len(result.errors) == 1
        assert "TICK3" in result.errors[0]
        assert "Erro maluco" in result.errors[0]

    def test_functional_full_flow(self, pipeline, ref_date):
        sample_path = os.path.join(
            os.path.dirname(__file__), 
            "..", "..", "..", "..", "samples", "Exemplo_Ativos_B3.csv"
        )
        sample_path = os.path.normpath(sample_path)
        
        if not os.path.exists(sample_path):
            pytest.skip(f"Arquivo não encontrado: {sample_path}")
            
        result = pipeline.execute(sample_path, ref_date)
        
        assert result.status == "SUCCESS", f"Erros encontrados: {result.errors}"
        assert len(result.errors) == 0
        assert result.processed_count > 0
        assert result.discarded_count == 0
        
        # Garante que os snapshots são gerados e validados
        assert len(result.snapshots) == result.processed_count
        assert hasattr(result.snapshots[0], "snapshot_hash")
        assert result.snapshots[0].source_system == "B3_AREA_INVESTIDOR"
        assert result.snapshots[0].reference_date == ref_date
