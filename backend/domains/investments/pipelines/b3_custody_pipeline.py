import time
import logging
from datetime import date
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.domains.investments.dto import PositionSnapshot
from backend.domains.investments.readers.b3_reader import B3CustodyReader, B3ReaderException
from backend.domains.investments.parsers.b3_parser import B3CustodyParser, B3ParserException
from backend.domains.investments.normalizers.b3_normalizer import B3CustodyNormalizer

logger = logging.getLogger(__name__)

class PipelineResult(BaseModel):
    snapshots: List[PositionSnapshot] = Field(default_factory=list)
    execution_time_ms: float = 0.0
    processed_count: int = 0
    discarded_count: int = 0
    persisted_count: int = 0
    errors: List[str] = Field(default_factory=list)
    status: str = "SUCCESS"

class B3CustodyPipeline:
    """
    Orquestrador responsável por extrair dados da Área do Investidor (B3),
    parser linhas e normalizar os ativos gerando uma lista estática de Snapshots.
    
    Atenção: 
    - Não aplica regras de negócio (Valuation, Reconciliação).
    - Persistência é opcional: passar `repository` ativa o UPSERT automático.
    """
    
    def __init__(
        self, 
        reader: Optional[B3CustodyReader] = None,
        parser: Optional[B3CustodyParser] = None,
        normalizer: Optional[B3CustodyNormalizer] = None,
        repository=None  # Optional[PositionRepository] — desacoplado via duck typing
    ):
        self.reader = reader or B3CustodyReader()
        self.parser = parser or B3CustodyParser()
        self.normalizer = normalizer or B3CustodyNormalizer()
        self.repository = repository
        
    def execute(self, file_path: str, reference_date: date) -> PipelineResult:
        start_time = time.time()
        result = PipelineResult()
        
        try:
            logger.info(f"Iniciando Pipeline B3 Custódia para {file_path} (Data Base: {reference_date})")
            
            # 1. Reader -> Dictionary of DataFrames
            dataframes = self.reader.read(file_path)
            
            # 2. Parser -> Typed DTOs
            raw_dtos = self.parser.parse(dataframes)
            
            # 3. Normalizer -> PositionSnapshots
            snapshots = []
            
            # Process Ações
            if "Posição - Ações" in raw_dtos:
                for raw in raw_dtos["Posição - Ações"]:
                    try:
                        snapshots.append(self.normalizer.normalize_stock(raw, reference_date))
                    except Exception as e:
                        result.errors.append(f"Erro ao normalizar Ação {raw.codigo_negociacao}: {str(e)}")
                        result.discarded_count += 1
                        
            # Process Fundos
            if "Posição - Fundos" in raw_dtos:
                for raw in raw_dtos["Posição - Fundos"]:
                    try:
                        snapshots.append(self.normalizer.normalize_fund(raw, reference_date))
                    except Exception as e:
                        result.errors.append(f"Erro ao normalizar Fundo {raw.codigo_negociacao}: {str(e)}")
                        result.discarded_count += 1
                        
            # Process Tesouro
            if "Posição - Tesouro Direto" in raw_dtos:
                for raw in raw_dtos["Posição - Tesouro Direto"]:
                    try:
                        snapshots.append(self.normalizer.normalize_treasury(raw, reference_date))
                    except Exception as e:
                        result.errors.append(f"Erro ao normalizar Tesouro {raw.codigo_isin}: {str(e)}")
                        result.discarded_count += 1
            
            # (Proventos são ignorados intencionalmente nesta etapa de PositionSnapshot)
            
            result.snapshots = snapshots
            result.processed_count = len(snapshots)
            
            # Persistência opcional: ativada se repository foi injetado
            if self.repository is not None and snapshots:
                try:
                    result.persisted_count = self.repository.save_many(snapshots)
                except Exception as e:
                    result.errors.append(f"Erro na persistência: {str(e)}")
                    result.status = "PARTIAL_SUCCESS"
                    result.execution_time_ms = (time.time() - start_time) * 1000.0
                    return result
            
            if result.errors:
                result.status = "PARTIAL_SUCCESS" if result.processed_count > 0 else "FAILED"
            
        except (B3ReaderException, B3ParserException) as e:
            logger.error(f"Erro no pipeline B3: {str(e)}")
            result.errors.append(str(e))
            result.status = "FAILED"
        except FileNotFoundError as e:
            logger.error(f"Arquivo não encontrado: {str(e)}")
            result.errors.append(str(e))
            result.status = "FAILED"
        except Exception as e:
            logger.exception("Erro crítico não mapeado no Pipeline B3")
            result.errors.append(f"Erro crítico sistêmico: {str(e)}")
            result.status = "FAILED"
            
        result.execution_time_ms = (time.time() - start_time) * 1000.0
        return result
