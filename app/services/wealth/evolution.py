from sqlalchemy.orm import Session
from sqlalchemy import func, Integer, extract
from app.models.wealth import PortfolioEvolution, Benchmark
from typing import Dict, Any

class EvolutionService:
    def __init__(self, db: Session):
        self.db = db

    def get_evolution_and_alpha(self, month: str, benchmark_type: str = "CDI") -> Dict[str, Any]:
        """
        Retorna a evolução do patrimônio para o mês e calcula o Alpha contra o Benchmark escolhido.
        Alpha = Rentabilidade Acumulada do Portfolio - Rentabilidade Acumulada do Benchmark.
        Para simplificar neste slice, usaremos o valor_pct do Benchmark do mês.
        """
        # Formato mês: "YYYY-MM"
        year, month_num = month.split("-")
        
        evolution = self.db.query(PortfolioEvolution).filter(
            extract('year', PortfolioEvolution.reference_month) == int(year),
            extract('month', PortfolioEvolution.reference_month) == int(month_num)
        ).first()

        if not evolution:
            return {"error": "Sem evolução patrimonial no período solicitado."}

        benchmark = self.db.query(Benchmark).filter(
            Benchmark.type == benchmark_type,
            extract('year', Benchmark.reference_date) == int(year),
            extract('month', Benchmark.reference_date) == int(month_num)
        ).first()

        portfolio_return = evolution.rentabilidade_mensal_pct
        benchmark_return = benchmark.value_pct if benchmark else 0.0
        
        alpha = portfolio_return - benchmark_return

        return {
            "month": month,
            "portfolio_patrimonio_cents": evolution.patrimonio_cents,
            "portfolio_return_pct": portfolio_return,
            "benchmark_type": benchmark_type,
            "benchmark_return_pct": benchmark_return,
            "alpha": alpha
        }
