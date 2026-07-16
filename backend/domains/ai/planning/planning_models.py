from pydantic import BaseModel, Field
from typing import List, Optional

class GoalDTO(BaseModel):
    id: Optional[str] = None
    goal_name: str
    target_amount: float
    current_amount: Optional[float] = 0.0
    monthly_contribution: float
    expected_return: float
    target_date: str
    active: bool = True

class SimulationRequestDTO(BaseModel):
    goal_id: str
    scenario: str = "Moderado" # Conservador, Moderado, Otimista
    aporte_adjustment: Optional[float] = 1.0 # 1.0 = atual, 1.2 = aumento de 20%, 0.8 = reducao de 20%

class ProjectionPoint(BaseModel):
    year: int
    projected_value: float
    projected_dividends: float

class SimulationResponseDTO(BaseModel):
    goal_name: str
    scenario: str
    time_to_independence_years: Optional[float]
    projections: List[ProjectionPoint]
    ai_analysis: str
    tokens: int
    latency: float
