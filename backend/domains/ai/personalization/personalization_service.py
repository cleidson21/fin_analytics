import logging
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.domains.ai.providers.gemini_provider import GeminiProvider
from backend.domains.ai.personalization.personalization_models import PersonalizationDTO, PersonalizationRecord
from backend.domains.ai.personalization.personalization_repository import PersonalizationRepository

logger = logging.getLogger(__name__)

PERSONALIZATION_SYSTEM_PROMPT = """
Você é o Personalization Engine do FINANALYTICS V3.
Sua missão é determinar a configuração ideal de experiência de usuário com base no histórico comportamental.
Você não emite conselhos financeiros, nem alertas.
Você APENAS produz parâmetros de interface, comunicação e priorização.
A saída deve ser RIGOROSAMENTE em formato JSON (sem quebras de linha fora do json).

[PERFIL E COMPORTAMENTO]
Memória Financeira:
{memory}

Perfil Financeiro Atual:
{profile}

Último Coach:
{coach}

Último Executive Brief:
{executive}

Insights Ativos:
{insights}

Gere o seguinte schema JSON (sem quebras de linha fora do json):
{{
  "communication_style": "técnico | executivo | resumido | detalhado",
  "detail_level": "alto | médio | baixo",
  "priority_topics": ["patrimônio", "dividendos", "planejamento", "risco", "alocação"],
  "dashboard_focus": ["metas", "evolução patrimonial", "risco"],
  "preferred_frequency": "diária | semanal | mensal",
  "notification_preferences": ["alertas de risco", "alertas de dividendos"],
  "learning_preferences": ["educação passiva", "educação proativa"],
  "language_profile": "Linguagem corporativa | Linguagem simples",
  "summary_preferences": "Preferência por resumos visuais ou textuais"
}}
"""

class AIPersonalizationService:
    def __init__(self, provider: GeminiProvider, repository: PersonalizationRepository):
        self.provider = provider
        self.repository = repository

    def get_personalization(self, session: Session) -> PersonalizationDTO:
        self.repository.ensure_table_exists(session)
        record = self.repository.get_latest_personalization(session)
        
        if not record:
            record = self.generate_personalization(session)
            if not record:
                return PersonalizationDTO(
                    communication_style="padrão", detail_level="médio", 
                    priority_topics=[], dashboard_focus=[], 
                    preferred_frequency="semanal", generated_at=datetime.now(timezone.utc).isoformat()
                )
                
        try:
            topics = json.loads(record.priority_topics)
        except: topics = []
        try:
            dash = json.loads(record.dashboard_focus)
        except: dash = []
            
        return PersonalizationDTO(
            communication_style=record.communication_style,
            detail_level=record.detail_level,
            priority_topics=topics,
            dashboard_focus=dash,
            preferred_frequency=record.preferred_frequency,
            generated_at=record.generated_at
        )

    def generate_personalization(self, session: Session) -> PersonalizationRecord:
        self.repository.ensure_table_exists(session)
        
        context = self.repository.get_context(session)
        cache_key = context["cache_key"]
        
        latest = self.repository.get_latest_personalization(session)
        if latest and latest.cache_key == cache_key:
            logger.info(f"Personalization cache hit for {cache_key}. Skipping generation.")
            return latest
            
        version = (latest.personalization_version + 1) if latest else 1
            
        prompt = PERSONALIZATION_SYSTEM_PROMPT.format(
            memory=json.dumps(context["memory"]),
            profile=json.dumps(context["profile"]),
            coach=json.dumps(context["coach"]),
            executive=json.dumps(context["executive"]),
            insights=json.dumps(context["insights"])
        )
        
        try:
            response = self.provider.generate_json(prompt)
            if not response.success or not response.data:
                logger.warning("Failed to get JSON response for Personalization.")
                return None
                
            data = response.data
            now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            
            record = PersonalizationRecord(
                id=str(uuid.uuid4()),
                personalization_version=version,
                communication_style=data.get("communication_style", "padrão"),
                detail_level=data.get("detail_level", "médio"),
                priority_topics=json.dumps(data.get("priority_topics", [])),
                dashboard_focus=json.dumps(data.get("dashboard_focus", [])),
                preferred_frequency=data.get("preferred_frequency", "semanal"),
                notification_preferences=json.dumps(data.get("notification_preferences", [])),
                learning_preferences=json.dumps(data.get("learning_preferences", [])),
                language_profile=data.get("language_profile", "Linguagem simples"),
                summary_preferences=data.get("summary_preferences", "Visuais"),
                generated_at=now,
                expires_at=None,
                cache_key=cache_key
            )
            
            self.repository.save_personalization(session, record)
            return record
            
        except Exception as e:
            logger.error(f"Error generating Personalization: {e}", exc_info=True)
            return None
