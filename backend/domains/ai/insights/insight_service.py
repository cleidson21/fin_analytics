import logging
import json
import uuid
from datetime import datetime, timezone
from typing import List
from sqlalchemy.orm import Session
from backend.domains.ai.providers.gemini_provider import GeminiProvider
from backend.domains.ai.insights.insight_models import InsightDTO, AIInsightGenerationResult
from backend.domains.ai.insights.insight_repository import InsightRepository

logger = logging.getLogger(__name__)

INSIGHTS_SYSTEM_PROMPT = """
Você é o Motor de Insights Proativos do FINANALYTICS V3.
Você analisa dados do patrimônio do usuário e gera Alertas e Insights de forma passiva.
NÃO faça recomendações de compra ou venda específicas (como 'Compre ITSA4'). Use tom educacional e financeiro.
Sua saída DEVE ser ESTRITAMENTE EM JSON, contendo uma lista de objetos, onde a raiz do objeto json seja 'insights', que contém a lista.
Cada objeto da lista deve conter: 'insight_type' (Patrimonio, Dividendos, Carteira, Mercado, Performance), 'severity' (info, warning, success), 'title', 'description', 'recommendation'.

[CONTEXTO ATUAL DO USUÁRIO]
Histórico Recente de Patrimônio e Dividendos (Últimos 3 registros):
{portfolio_history}

Alocação da Carteira (%):
{allocation}

Indicadores Macroeconômicos Atuais:
{macro}

Baseie-se nesses dados. Gere de 1 a 4 insights relevantes (ex: concentração alta em alguma classe, crescimento de dividendos, caixa alto, macro).
"""

class AIInsightService:
    def __init__(self, provider: GeminiProvider, repository: InsightRepository):
        self.provider = provider
        self.repository = repository

    def get_insights(self, session: Session) -> List[InsightDTO]:
        self.repository.ensure_table_exists(session)
        return self.repository.get_active_insights(session)

    def generate_proactive_insights(self, session: Session) -> List[InsightDTO]:
        self.repository.ensure_table_exists(session)
        
        dates = self.repository.get_latest_context_dates(session)
        cache_key = f"{dates['snapshot_date']}|{dates['macro_date']}"
        
        if self.repository.has_insights_for_cache(session, cache_key):
            logger.info(f"Insights up to date for cache_key {cache_key}. Skipping generation.")
            return []

        # Gather context
        portfolio = self.repository.get_portfolio_summary(session)
        allocation = self.repository.get_allocation_summary(session)
        macro = self.repository.get_macro_summary(session)
        
        if not portfolio:
            logger.info("Not enough data to generate insights.")
            return []
            
        prompt = INSIGHTS_SYSTEM_PROMPT.format(
            portfolio_history=json.dumps(portfolio),
            allocation=json.dumps(allocation),
            macro=json.dumps(macro)
        )
        
        try:
            response = self.provider.generate_json(prompt)
            if not response.success or not response.data:
                raise ValueError("Failed to get valid JSON from Gemini.")
                
            insights_data = response.data.get("insights", [])
            new_insights = []
            
            for item in insights_data:
                new_insights.append(InsightDTO(
                    id=str(uuid.uuid4()),
                    insight_type=item.get("insight_type", "Geral"),
                    severity=item.get("severity", "info"),
                    title=item.get("title", "Novo Insight"),
                    description=item.get("description", ""),
                    recommendation=item.get("recommendation", ""),
                    source_tables=["portfolio_snapshots", "asset_valuations", "macro_indicators"],
                    generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    expires_at=None,
                    dismissed=False
                ))
                
            if new_insights:
                self.repository.save_insights(session, new_insights, cache_key)
                
            return new_insights
            
        except Exception as e:
            logger.error(f"Failed to generate proactive insights: {e}")
            raise
