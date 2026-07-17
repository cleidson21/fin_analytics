import logging
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.domains.ai.providers.gemini_provider import GeminiProvider
from backend.domains.ai.coach.coach_models import CoachDTO, CoachRecord
from backend.domains.ai.coach.coach_repository import CoachRepository

logger = logging.getLogger(__name__)

COACH_SYSTEM_PROMPT = """
Você é o Financial Coach do FINANALYTICS V3.
Sua missão é atuar como mentor do investidor, propondo planos de ação claros, prioridades reais e hábitos saudáveis.
Você interpreta as análises geradas pelos outros módulos de IA. Nunca recalcula nada.
Sempre utilize tom consultivo e amigável.
A saída deve ser RIGOROSAMENTE em formato JSON (sem quebras de linha fora do json).

[CONTEXTO DE COACHING]
Perfil Financeiro (DNA):
{profile}

Executive Brief (Último resumo diário):
{executive}

Alertas e Anomalias (Insights ativos):
{insights}

Simulações Atuais:
{planning}

Cenário Macro:
{macro}

Gere o seguinte schema JSON (sem quebras de linha fora do json):
{{
  "action_plan": "1 parágrafo com o parecer geral do coach.",
  "weekly_focus": "A maior prioridade para a semana.",
  "monthly_focus": "O foco estratégico para o mês.",
  "priority_actions": ["Ação imediata 1", "Ação imediata 2", "Ação imediata 3"],
  "recommended_habits": ["Hábito sugerido 1", "Hábito sugerido 2"],
  "portfolio_observations": "Observação sobre a alocação frente ao perfil.",
  "risk_observations": "Alerta qualitativo de risco.",
  "planning_observations": "Considerações sobre as metas de longo prazo."
}}
"""

class AICoachService:
    def __init__(self, provider: GeminiProvider, repository: CoachRepository):
        self.provider = provider
        self.repository = repository

    def get_financial_coach_plan(self, session: Session) -> CoachDTO:
        self.repository.ensure_table_exists(session)
        record = self.repository.get_latest_coach_plan(session)
        
        if not record:
            # Sync generation on first access
            record = self.generate_coach_plan(session)
            if not record:
                return CoachDTO(
                    weekly_focus="N/A", monthly_focus="N/A", 
                    priority_actions=[], recommended_habits=[], 
                    generated_at=datetime.now(timezone.utc).isoformat()
                )
                
        try:
            priorities = json.loads(record.priority_actions)
        except:
            priorities = []
            
        try:
            habits = json.loads(record.recommended_habits)
        except:
            habits = []
            
        return CoachDTO(
            weekly_focus=record.weekly_focus,
            monthly_focus=record.monthly_focus,
            priority_actions=priorities,
            recommended_habits=habits,
            generated_at=record.generated_at
        )

    def generate_coach_plan(self, session: Session) -> CoachRecord:
        self.repository.ensure_table_exists(session)
        
        context = self.repository.get_context(session)
        cache_key = context["cache_key"]
        
        latest = self.repository.get_latest_coach_plan(session)
        if latest and latest.cache_key == cache_key:
            logger.info(f"Coach Plan cache hit for {cache_key}. Skipping generation.")
            return latest
            
        version = (latest.coach_version + 1) if latest else 1
            
        prompt = COACH_SYSTEM_PROMPT.format(
            profile=json.dumps(context["profile"]),
            executive=json.dumps(context["executive"]),
            planning=json.dumps(context["planning"]),
            insights=json.dumps(context["insights"]),
            macro=json.dumps(context["macro"])
        )
        
        try:
            response = self.provider.generate_json(prompt)
            if not response.success or not response.data:
                logger.warning("Failed to get JSON response for Coach Plan.")
                return None
                
            data = response.data
            now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            
            record = CoachRecord(
                id=str(uuid.uuid4()),
                coach_version=version,
                action_plan=data.get("action_plan", "Sem plano."),
                weekly_focus=data.get("weekly_focus", "N/A"),
                monthly_focus=data.get("monthly_focus", "N/A"),
                recommended_habits=json.dumps(data.get("recommended_habits", [])),
                priority_actions=json.dumps(data.get("priority_actions", [])),
                portfolio_observations=data.get("portfolio_observations", "N/A"),
                risk_observations=data.get("risk_observations", "N/A"),
                planning_observations=data.get("planning_observations", "N/A"),
                generated_at=now,
                expires_at=None,
                cache_key=cache_key
            )
            
            self.repository.save_coach_plan(session, record)
            return record
            
        except Exception as e:
            logger.error(f"Error generating Coach Plan: {e}", exc_info=True)
            return None
