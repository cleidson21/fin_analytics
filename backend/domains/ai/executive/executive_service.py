import logging
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.domains.ai.providers.gemini_provider import GeminiProvider
from backend.domains.ai.executive.executive_models import ExecutiveBriefDTO, ExecutiveBriefRecord
from backend.domains.ai.executive.executive_repository import ExecutiveRepository

logger = logging.getLogger(__name__)

EXECUTIVE_SYSTEM_PROMPT = """
Você é o Copiloto Executivo do FINANALYTICS V3.
Sua missão é gerar um Executive Brief diário consolidando a posição financeira do investidor.
Você não executa cálculos. Você apenas consolida, sumariza e prioriza.
A saída deve ser RIGOROSAMENTE em formato JSON.

[CONTEXTO CONSOLIDADO]
Patrimônio e Alocação:
{portfolio}

Mercado Atual:
{macro}

Insights Recentes:
{insights}

Simulações de Planejamento:
{planning}

Gere o seguinte schema JSON (sem quebras de linha fora do json):
{{
  "summary": "Resumo executivo de 2 parágrafos sobre a situação global.",
  "portfolio_summary": "Análise da alocação e crescimento.",
  "market_summary": "Impacto da SELIC/IPCA/CDI na carteira atual.",
  "insights_summary": "Resumo das últimas anomalias detectadas.",
  "planning_summary": "Status das metas e simulações.",
  "risk_summary": "Exposição ao risco e liquidez.",
  "recommended_focus": "Lista com top 3 prioridades separadas por vírgula."
}}
"""

class AIExecutiveService:
    def __init__(self, provider: GeminiProvider, repository: ExecutiveRepository):
        self.provider = provider
        self.repository = repository

    def get_executive_brief(self, session: Session) -> ExecutiveBriefDTO:
        self.repository.ensure_table_exists(session)
        record = self.repository.get_latest_brief(session)
        if not record:
            # If no brief exists yet, try to generate one synchronously (first time only)
            record = self.generate_executive_brief(session)
            if not record:
                # Return empty fallback
                return ExecutiveBriefDTO(
                    summary="Nenhum dado disponível ainda.",
                    portfolio={}, market={}, insights=[], planning={}, priorities=[],
                    generated_at=datetime.now(timezone.utc).isoformat()
                )
                
        # Parse recommended_focus into priorities list
        priorities = [p.strip() for p in record.recommended_focus.split(",") if p.strip()]
        
        return ExecutiveBriefDTO(
            summary=record.summary,
            portfolio={"summary": record.portfolio_summary},
            market={"summary": record.market_summary},
            insights=[{"summary": record.insights_summary}],
            planning={"summary": record.planning_summary},
            priorities=priorities,
            generated_at=record.generated_at
        )

    def generate_executive_brief(self, session: Session) -> ExecutiveBriefRecord:
        self.repository.ensure_table_exists(session)
        
        context = self.repository.get_context(session)
        cache_key = context["cache_key"]
        
        latest = self.repository.get_latest_brief(session)
        if latest and latest.cache_key == cache_key:
            logger.info(f"Executive Brief cache hit for {cache_key}. Skipping generation.")
            return latest
            
        prompt = EXECUTIVE_SYSTEM_PROMPT.format(
            portfolio=json.dumps(context["portfolio"]),
            macro=json.dumps(context["macro"]),
            insights=json.dumps(context["insights"]),
            planning=json.dumps(context["planning"])
        )
        
        try:
            response = self.provider.generate_json(prompt)
            if not response.success or not response.data:
                logger.warning("Failed to get JSON response for Executive Brief.")
                return None
                
            data = response.data
            now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            
            record = ExecutiveBriefRecord(
                id=str(uuid.uuid4()),
                brief_date=now[:10],
                summary=data.get("summary", "Resumo indisponível."),
                portfolio_summary=data.get("portfolio_summary", ""),
                market_summary=data.get("market_summary", ""),
                insights_summary=data.get("insights_summary", ""),
                planning_summary=data.get("planning_summary", ""),
                risk_summary=data.get("risk_summary", ""),
                recommended_focus=data.get("recommended_focus", ""),
                generated_at=now,
                expires_at=None,
                cache_key=cache_key
            )
            
            self.repository.save_brief(session, record)
            return record
            
        except Exception as e:
            logger.error(f"Error generating Executive Brief: {e}", exc_info=True)
            return None
