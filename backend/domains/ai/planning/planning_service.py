import logging
import json
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.domains.ai.providers.gemini_provider import GeminiProvider
from backend.domains.ai.planning.planning_models import (
    GoalDTO, SimulationRequestDTO, SimulationResponseDTO, ProjectionPoint
)
from backend.domains.ai.planning.planning_repository import PlanningRepository

logger = logging.getLogger(__name__)

# Cache memory for planning (Hash based on goal_id + snapshot_date + scenario + aporte)
_planning_cache = {}

PLANNING_SYSTEM_PROMPT = """
Você é o Planejador Financeiro Inteligente do FINANALYTICS V3.
Você não executa cálculos, apenas interpreta as projeções atuariais geradas pelo simulador do sistema.
Analise os números abaixo e escreva uma interpretação consultiva, destacando se a meta é factível, se os dividendos cobrem os aportes e quanto tempo demorará.
NÃO recommende compra ou venda de ativos específicos. Seja encorajador porém realista.

[DADOS DA SIMULAÇÃO]
Patrimônio Atual: R$ {patrimonio:.2f}
Aporte Mensal Simulado: R$ {aporte:.2f}
Cenário: {cenario}
Meta Financeira: R$ {meta:.2f}

[PROJEÇÕES]
{projecoes}

[INDICADORES MACRO]
{macro}

A resposta deve ser estritamente em JSON, contendo apenas a chave 'ai_analysis' (string).
"""

class AIPlanningService:
    def __init__(self, provider: GeminiProvider, repository: PlanningRepository):
        self.provider = provider
        self.repository = repository

    def _apply_scenario_modifier(self, base_rate: float, scenario: str) -> float:
        if scenario.lower() == "conservador":
            return base_rate * 0.7 # Penalize return
        elif scenario.lower() == "otimista":
            return base_rate * 1.3
        return base_rate # Moderado

    def _simulate_growth(self, initial_equity: float, monthly_contribution: float, annual_return: float, years: List[int]) -> List[ProjectionPoint]:
        monthly_rate = (1 + annual_return) ** (1/12) - 1
        projections = []
        
        for y in sorted(years):
            months = y * 12
            # FV = PV*(1+i)^n + PMT*(((1+i)^n - 1)/i)
            if monthly_rate > 0:
                future_value = initial_equity * ((1 + monthly_rate) ** months) + \
                               monthly_contribution * (((1 + monthly_rate) ** months - 1) / monthly_rate)
            else:
                future_value = initial_equity + (monthly_contribution * months)
                
            # Assume constant Dividend Yield based on 5% standard if no data, or historical
            dy = 0.05
            projected_div_annual = future_value * dy
            
            projections.append(ProjectionPoint(
                year=y,
                projected_value=round(future_value, 2),
                projected_dividends=round(projected_div_annual, 2)
            ))
            
        return projections

    def _calculate_time_to_independence(self, initial: float, monthly: float, annual_return: float, target: float) -> Optional[float]:
        if initial >= target:
            return 0.0
        
        monthly_rate = (1 + annual_return) ** (1/12) - 1
        months = 0
        current = initial
        
        # Max simulation 100 years
        while current < target and months < 1200:
            current = current * (1 + monthly_rate) + monthly
            months += 1
            
        if months >= 1200:
            return None
        return round(months / 12, 1)

    def simulate_goal(self, session: Session, request: SimulationRequestDTO) -> SimulationResponseDTO:
        self.repository.ensure_tables_exist(session)
        
        goal = self.repository.get_goal_by_id(session, request.goal_id)
        if not goal:
            raise ValueError(f"Goal {request.goal_id} not found")
            
        context = self.repository.get_portfolio_context(session)
        macro = self.repository.get_macro_context(session)
        
        snapshot_date = context["snapshot_date"]
        # Allow simulation even if no wealth is recorded yet.
        initial_equity = context["equity"] or goal.current_amount or 0.0
        
        aporte_simulado = goal.monthly_contribution * (request.aporte_adjustment or 1.0)
        
        # Scenario adjusted return
        rate = self._apply_scenario_modifier(goal.expected_return, request.scenario)
        
        # Caching logic
        hash_raw = f"{goal.id}|{snapshot_date}|{request.scenario}|{request.aporte_adjustment}"
        sim_hash = hashlib.sha256(hash_raw.encode('utf-8')).hexdigest()
        
        if sim_hash in _planning_cache:
            logger.info("Simulation cache hit.")
            cached = _planning_cache[sim_hash]
            return SimulationResponseDTO(
                goal_name=goal.goal_name,
                scenario=request.scenario,
                time_to_independence_years=cached["time_to_independence"],
                projections=[ProjectionPoint(**p) for p in cached["projections"]],
                ai_analysis=cached["ai_analysis"],
                tokens=0,
                latency=0.0
            )

        # 1. Projections
        projections = self._simulate_growth(initial_equity, aporte_simulado, rate, [1, 5, 10, 20])
        
        # 2. Independence
        time_to_indep = self._calculate_time_to_independence(initial_equity, aporte_simulado, rate, goal.target_amount)
        
        # Save simulations in DB to obey constraints
        for p in projections:
            self.repository.save_simulation(session, goal.id, sim_hash, p.year, p.projected_value, request.scenario)
            
        # AI Interpretation
        prompt = PLANNING_SYSTEM_PROMPT.format(
            patrimonio=initial_equity,
            aporte=aporte_simulado,
            cenario=request.scenario,
            meta=goal.target_amount,
            projecoes=json.dumps([p.model_dump() for p in projections]),
            macro=json.dumps(macro)
        )
        
        response = self.provider.generate_json(prompt)
        ai_text = ""
        if response.success and response.data:
            ai_text = response.data.get("ai_analysis", "")
            
        # Cache Result
        _planning_cache[sim_hash] = {
            "time_to_independence": time_to_indep,
            "projections": [p.model_dump() for p in projections],
            "ai_analysis": ai_text
        }
        
        return SimulationResponseDTO(
            goal_name=goal.goal_name,
            scenario=request.scenario,
            time_to_independence_years=time_to_indep,
            projections=projections,
            ai_analysis=ai_text,
            tokens=response.tokens if response.success else 0,
            latency=response.latency if response.success else 0.0
        )
