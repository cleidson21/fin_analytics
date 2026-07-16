import logging
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.domains.ai.providers.gemini_provider import GeminiProvider
from backend.domains.ai.advisor.advisor_models import AdvisorRequestDTO, AdvisorResponseDTO, AdvisorContext
from backend.domains.ai.advisor.advisor_repository import AdvisorRepository

logger = logging.getLogger(__name__)

# Simple in-memory cache for advisor answers to avoid hitting API repeatedly for the same question + context
_advisor_cache = {}

ADVISOR_SYSTEM_PROMPT = """
Você é o Assistente Financeiro Inteligente do FINANALYTICS V3.
Você atua estritamente como consultor, usando linguagem clara e profissional.
NUNCA recomende a compra ou venda de ativos específicos (ex: compre dólar, invista em bitcoin).
Apenas analise os dados fornecidos abaixo e responda à pergunta do usuário baseando-se neles.

[CONTEXTO DO PORTFÓLIO]
Patrimônio Atual: R$ {patrimonio_atual:.2f}
Patrimônio Investido (Custo): R$ {patrimonio_investido:.2f}
Lucro/Prejuízo Líquido: R$ {patrimonio_liquido:.2f}
Dividendos Acumulados: R$ {dividendos_acumulados:.2f}
Rentabilidade Histórica (TWR): {rentabilidade_historica:.2f}%
Maior Posição Atual: {maior_posicao}
Menor Posição Atual: {menor_posicao}

[INDICADORES MACROECONÔMICOS]
{indicadores_macro}

[PERGUNTA DO USUÁRIO]
{question}
"""

class AIAdvisorService:
    def __init__(self, provider: GeminiProvider, repository: AdvisorRepository):
        self.provider = provider
        self.repository = repository

    def build_context(self, session: Session) -> AdvisorContext:
        snapshot = self.repository.get_latest_portfolio_snapshot(session)
        positions = self.repository.get_top_positions(session)
        macro = self.repository.get_latest_macro(session)
        
        # We calculate percentual_caixa based on logic if available, else 0 for now as requested
        # 'percentual_caixa' is requested in mandatory context, we can derive it if we had cash balances.
        
        return AdvisorContext(
            patrimonio_atual=snapshot["patrimonio_atual"],
            patrimonio_investido=snapshot["patrimonio_investido"],
            patrimonio_liquido=snapshot["patrimonio_liquido"],
            dividendos_acumulados=snapshot["dividendos_acumulados"],
            maior_posicao=positions["maior_posicao"],
            menor_posicao=positions["menor_posicao"],
            percentual_caixa=0.0, # Placeholder if no raw cash available in snapshot
            indicadores_macro=macro
        )

    def answer_question(self, session: Session, request: AdvisorRequestDTO) -> AdvisorResponseDTO:
        context_data = self.build_context(session)
        
        macro_str = json.dumps(context_data.indicadores_macro) if context_data.indicadores_macro else "Não disponível"
        
        prompt = ADVISOR_SYSTEM_PROMPT.format(
            patrimonio_atual=context_data.patrimonio_atual,
            patrimonio_investido=context_data.patrimonio_investido,
            patrimonio_liquido=context_data.patrimonio_liquido,
            dividendos_acumulados=context_data.dividendos_acumulados,
            rentabilidade_historica=0.0, # Add to prompt formatting if fetched, wait it's in snapshot
            maior_posicao=context_data.maior_posicao or "N/A",
            menor_posicao=context_data.menor_posicao or "N/A",
            indicadores_macro=macro_str,
            question=request.question
        )
        
        snapshot = self.repository.get_latest_portfolio_snapshot(session)
        # Update formatting with proper variables
        prompt = ADVISOR_SYSTEM_PROMPT.format(
            patrimonio_atual=context_data.patrimonio_atual,
            patrimonio_investido=context_data.patrimonio_investido,
            patrimonio_liquido=context_data.patrimonio_liquido,
            dividendos_acumulados=context_data.dividendos_acumulados,
            rentabilidade_historica=snapshot.get("rentabilidade_historica", 0.0), 
            maior_posicao=context_data.maior_posicao or "Nenhuma",
            menor_posicao=context_data.menor_posicao or "Nenhuma",
            indicadores_macro=macro_str,
            question=request.question
        )
        
        # Enforce JSON output for standard compliance
        prompt_with_schema = prompt + "\nRESPONDA EM JSON COM AS CHAVES: 'answer' (string com a resposta)."
        
        # Check cache
        import hashlib
        prompt_hash = hashlib.sha256(prompt_with_schema.encode('utf-8')).hexdigest()
        
        if prompt_hash in _advisor_cache:
            logger.info("Advisor Cache hit.")
            cached_data = _advisor_cache[prompt_hash]
            return AdvisorResponseDTO(
                answer=cached_data["answer"],
                sources=["portfolio_snapshots", "asset_valuations", "macro_indicators"],
                generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                model=cached_data["model"],
                latency=0.0,
                tokens=0
            )
            
        response = self.provider.generate_json(prompt_with_schema)
        
        if not response.success or not response.data:
            raise ValueError("Failed to get a valid response from Gemini.")
            
        answer_text = response.data.get("answer", "")
        
        # Save to cache
        _advisor_cache[prompt_hash] = {
            "answer": answer_text,
            "model": response.model
        }
        
        return AdvisorResponseDTO(
            answer=answer_text,
            sources=["portfolio_snapshots", "asset_valuations", "macro_indicators"],
            generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            model=response.model,
            latency=response.latency,
            tokens=response.tokens
        )
