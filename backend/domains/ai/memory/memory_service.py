import logging
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.domains.ai.providers.gemini_provider import GeminiProvider
from backend.domains.ai.memory.memory_models import MemoryDTO, MemoryRecord
from backend.domains.ai.memory.memory_repository import MemoryRepository

logger = logging.getLogger(__name__)

MEMORY_SYSTEM_PROMPT = """
Você é o Financial Memory Engine do FINANALYTICS V3.
Sua missão é deduzir o comportamento de longo prazo, evolução e padrões do investidor a partir do histórico consolidado.
Você não emite recomendações. Você apenas traça o perfil histórico (A Memória).
A saída deve ser RIGOROSAMENTE em formato JSON (sem quebras de linha fora do json).

[HISTÓRICO COMPORTAMENTAL]
Tempo de Vida da Carteira:
{portfolio}

Evolução do Perfil (Últimas análises):
{profile}

Histórico de Coaching (Focos anteriores):
{coach}

Resumos Executivos Anteriores:
{executive}

Histórico de Planejamento:
{planning}

Gere o seguinte schema JSON (sem quebras de linha fora do json):
{{
  "investment_preferences": ["Preferência 1", "Preferência 2"],
  "behavior_patterns": ["Padrão detectado 1", "Padrão detectado 2"],
  "historical_strengths": ["Ponto forte histórico 1", "Ponto forte histórico 2"],
  "historical_attention_points": ["Ponto de atenção crônico 1"],
  "recurring_goals": ["Meta 1", "Meta 2"],
  "learning_summary": "1 parágrafo resumindo a evolução comportamental do investidor ao longo do tempo.",
  "confidence_score": 0.95
}}
"""

class AIMemoryService:
    def __init__(self, provider: GeminiProvider, repository: MemoryRepository):
        self.provider = provider
        self.repository = repository

    def get_financial_memory(self, session: Session) -> MemoryDTO:
        self.repository.ensure_table_exists(session)
        record = self.repository.get_latest_memory(session)
        
        if not record:
            # Sync generation on first access
            record = self.generate_memory(session)
            if not record:
                return MemoryDTO(
                    investment_preferences=[], behavior_patterns=[], 
                    historical_strengths=[], historical_attention_points=[], 
                    confidence_score=0.0, generated_at=datetime.now(timezone.utc).isoformat()
                )
                
        try:
            prefs = json.loads(record.investment_preferences)
        except: prefs = []
        try:
            patterns = json.loads(record.behavior_patterns)
        except: patterns = []
        try:
            strengths = json.loads(record.historical_strengths)
        except: strengths = []
        try:
            attention = json.loads(record.historical_attention_points)
        except: attention = []
            
        return MemoryDTO(
            investment_preferences=prefs,
            behavior_patterns=patterns,
            historical_strengths=strengths,
            historical_attention_points=attention,
            confidence_score=record.confidence_score,
            generated_at=record.generated_at
        )

    def generate_memory(self, session: Session) -> MemoryRecord:
        self.repository.ensure_table_exists(session)
        
        context = self.repository.get_context(session)
        cache_key = context["cache_key"]
        
        latest = self.repository.get_latest_memory(session)
        if latest and latest.cache_key == cache_key:
            logger.info(f"Financial Memory cache hit for {cache_key}. Skipping generation.")
            return latest
            
        version = (latest.memory_version + 1) if latest else 1
            
        prompt = MEMORY_SYSTEM_PROMPT.format(
            portfolio=json.dumps(context["portfolio_summary"]),
            profile=json.dumps(context["profile_history"]),
            coach=json.dumps(context["coach_history"]),
            executive=json.dumps(context["executive_history"]),
            planning=json.dumps(context["planning_history"])
        )
        
        try:
            response = self.provider.generate_json(prompt)
            if not response.success or not response.data:
                logger.warning("Failed to get JSON response for Financial Memory.")
                return None
                
            data = response.data
            now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            
            record = MemoryRecord(
                id=str(uuid.uuid4()),
                memory_version=version,
                investment_preferences=json.dumps(data.get("investment_preferences", [])),
                behavior_patterns=json.dumps(data.get("behavior_patterns", [])),
                historical_strengths=json.dumps(data.get("historical_strengths", [])),
                historical_attention_points=json.dumps(data.get("historical_attention_points", [])),
                recurring_goals=json.dumps(data.get("recurring_goals", [])),
                learning_summary=data.get("learning_summary", "Sem dados suficientes."),
                confidence_score=float(data.get("confidence_score", 0.5)),
                generated_at=now,
                expires_at=None,
                cache_key=cache_key
            )
            
            self.repository.save_memory(session, record)
            return record
            
        except Exception as e:
            logger.error(f"Error generating Financial Memory: {e}", exc_info=True)
            return None
