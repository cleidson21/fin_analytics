from decimal import Decimal
from typing import List, Dict, Optional
from pydantic import BaseModel
from backend.domains.investments.engines.position_engine import PositionResult

class ValuationResult(BaseModel):
    ticker: str
    institution: str
    quantity: Decimal
    cost_basis: Decimal        # Valor Investido Original
    average_cost: Decimal      # Custo Unitário Médio
    current_price: Decimal     # Preço Unitário de Mercado
    market_value: Decimal      # Valor Total a Mercado (Qtd * Current Price)
    unrealized_gain: Decimal   # Ganho/Perda Bruta (Market Value - Cost Basis)
    unrealized_gain_percent: Decimal # Retorno Percentual

class ValuationEngine:
    """
    Motor de Mark-to-Market (MTM) Puro.
    Recebe posições contábeis (PositionResult) consolidadas e um mapa
    de preços de mercado atualizados para calcular rentabilidade e
    patrimônio marcado a mercado.
    """
    def calculate_valuation(
        self,
        positions: List[PositionResult],
        market_prices: Dict[str, Decimal]
    ) -> List[ValuationResult]:
        
        results = []
        for pos in positions:
            # Se a quantidade for <= 0, o ativo foi zerado. O Valuation a mercado é zero.
            if pos.quantity <= 0:
                results.append(ValuationResult(
                    ticker=pos.ticker,
                    institution=pos.institution,
                    quantity=Decimal('0'),
                    cost_basis=Decimal('0'),
                    average_cost=Decimal('0'),
                    current_price=Decimal('0'),
                    market_value=Decimal('0'),
                    unrealized_gain=Decimal('0'),
                    unrealized_gain_percent=Decimal('0')
                ))
                continue
                
            # Determina o preço de mercado.
            # Se o ativo não possuir cotação fornecida, marcamos a mercado pelo próprio custo 
            # de aquisição, evitando que o patrimônio despenque artificialmente para zero.
            # O ganho/perda neste caso será 0.
            current_price = market_prices.get(pos.ticker)
            
            # Se o dict explicitamente fornecer o valor 0 (ex: empresa faliu), 
            # nós aceitamos a perda de 100%. Se ele fornecer None ou a chave não existir, 
            # assumimos o custo.
            if current_price is None:
                current_price = pos.average_price
                
            # Calcula as métricas financeiras
            market_value = pos.quantity * current_price
            cost_basis = pos.invested_value
            
            unrealized_gain = market_value - cost_basis
            
            # Ganho Percentual
            if cost_basis > Decimal('0'):
                unrealized_gain_percent = (unrealized_gain / cost_basis) * Decimal('100')
            else:
                # Caso extremo onde o cost_basis é 0 mas há quantidade (ex: bônus integral)
                # Gain % teoricamente é infinito. Definimos 0 ou 100% convencionalmente.
                # Aqui retornamos 100% em representação simbólica se houver market_value, senão 0.
                unrealized_gain_percent = Decimal('100') if market_value > Decimal('0') else Decimal('0')

            results.append(ValuationResult(
                ticker=pos.ticker,
                institution=pos.institution,
                quantity=pos.quantity,
                cost_basis=cost_basis,
                average_cost=pos.average_price,
                current_price=current_price,
                market_value=market_value,
                unrealized_gain=unrealized_gain,
                unrealized_gain_percent=unrealized_gain_percent
            ))
            
        return results
