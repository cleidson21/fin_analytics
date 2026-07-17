import logging
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.domains.ai.providers.gemini_provider import GeminiProvider
from backend.domains.ai.profile.profile_models import ProfileDTO, ProfileRecord
from backend.domains.ai.profile.profile_repository import ProfileRepository

logger = logging.getLogger(__name__)

PROFILE_SYSTEM_PROMPT = """
Você é o Financial Profiler do FINANALYTICS V3.
Você analisa o histórico do investidor e constrói seu Perfil Financeiro.
Você não executa cálculos, apenas interpreta tendências passadas, comportamento de metas e alertas recorrentes.
A saída deve ser RIGOROSAMENTE em formato JSON (sem quebras de linha fora do json).

[CONTEXTO COMPORTAMENTAL]
Evolução Patrimonial (Últimos 6 snapshots):
{portfolio}

Metas e Simulações Frequentes:
{planning}

Prioridades Recorrentes (Executive Briefs):
{briefs}

Insights Acumulados:
{insights}

Cenário Macro:
{macro}

Gere o seguinte schema JSON (sem quebras de linha fora do json):
{{
  "investor_profile": "Conservador, Moderado ou Arrojado",
  "risk_tolerance": "Baixa, Média ou Alta",
  "investment_style": "Ex: Foco em dividendos, Crescimento, Híbrido",
  "portfolio_maturity": "Ex: Acumulação, Transição, Fruição",
  "diversification_score": "Ex: Baixa, Adequada, Alta",
  "cash_behavior": "Ex: Reserva alta, Totalmente alocado",
  "dividend_focus": "Ex: Primário, Secundário, Inexistente",
  "consistency_score": "Ex: Constante, Irregular",
  "planning_score": "Ex: Focado em longo prazo, Reativo",
  "macro_sensitivity": "Ex: Alta exposição a juros, Neutro",
  "behavior_summary": "1 parágrafo resumindo o comportamento do investidor.",
  "strengths": ["Ponto forte 1", "Ponto forte 2"],
  "attention_points": ["Ponto de atenção 1", "Ponto de atenção 2"]
}}
"""

class AIProfileService:
    def __init__(self, provider: GeminiProvider, repository: ProfileRepository):
        self.provider = provider
        self.repository = repository

    def get_financial_profile(self, session: Session) -> ProfileDTO:
        self.repository.ensure_table_exists(session)
        record = self.repository.get_latest_profile(session)
        
        if not record:
            # Sync generation on first access
            record = self.generate_financial_profile(session)
            if not record:
                return ProfileDTO(
                    profile="Desconhecido", investment_style="N/A", 
                    strengths=[], attention_points=[], generated_at=datetime.now(timezone.utc).isoformat()
                )
                
        try:
            strengths = json.loads(record.strengths)
        except:
            strengths = []
            
        try:
            attention_points = json.loads(record.attention_points)
        except:
            attention_points = []
            
        return ProfileDTO(
            profile=record.investor_profile,
            investment_style=record.investment_style,
            strengths=strengths,
            attention_points=attention_points,
            generated_at=record.generated_at
        )

    def generate_financial_profile(self, session: Session) -> ProfileRecord:
        self.repository.ensure_table_exists(session)
        
        context = self.repository.get_context(session)
        cache_key = context["cache_key"]
        
        latest = self.repository.get_latest_profile(session)
        if latest and latest.cache_key == cache_key:
            logger.info(f"Financial Profile cache hit for {cache_key}. Skipping generation.")
            return latest
            
        version = (latest.profile_version + 1) if latest else 1
            
        prompt = PROFILE_SYSTEM_PROMPT.format(
            portfolio=json.dumps(context["portfolio"]),
            planning=json.dumps(context["planning"]),
            briefs=json.dumps(context["briefs"]),
            insights=json.dumps(context["insights"]),
            macro=json.dumps(context["macro"])
        )
        
        try:
            response = self.provider.generate_json(prompt)
            if not response.success or not response.data:
                logger.warning("Failed to get JSON response for Financial Profile.")
                return None
                
            data = response.data
            now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            
            record = ProfileRecord(
                id=str(uuid.uuid4()),
                profile_version=version,
                investor_profile=data.get("investor_profile", "Desconhecido"),
                risk_tolerance=data.get("risk_tolerance", "Desconhecida"),
                investment_style=data.get("investment_style", "N/A"),
                portfolio_maturity=data.get("portfolio_maturity", "N/A"),
                diversification_score=data.get("diversification_score", "N/A"),
                cash_behavior=data.get("cash_behavior", "N/A"),
                dividend_focus=data.get("dividend_focus", "N/A"),
                consistency_score=data.get("consistency_score", "N/A"),
                planning_score=data.get("planning_score", "N/A"),
                macro_sensitivity=data.get("macro_sensitivity", "N/A"),
                behavior_summary=data.get("behavior_summary", ""),
                strengths=json.dumps(data.get("strengths", [])),
                attention_points=json.dumps(data.get("attention_points", [])),
                generated_at=now,
                expires_at=None,
                cache_key=cache_key
            )
            
            self.repository.save_profile(session, record)
            return record
            
        except Exception as e:
            logger.error(f"Error generating Financial Profile: {e}", exc_info=True)
            return None
