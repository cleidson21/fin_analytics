from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.domains.investments.repository import PositionRepository, DividendRepository
from backend.domains.investments.dto import PositionUIRepresentationDTO, DividendUIRepresentationDTO, PaginatedResponse

class PositionService:
    def __init__(self, session: Session):
        self.repository = PositionRepository(session)

    def list_positions(self, limit: int = 50, offset: int = 0) -> PaginatedResponse:
        raw_items = self.repository.list_positions(limit, offset)
        total = self.repository.count_positions()
        
        items = []
        for r in raw_items:
            valor_investido = r.get('valor_investido') or 0.0
            valor_atual = r.get('valor_atual') or 0.0
            ganho = float(valor_atual) - float(valor_investido)
            # Default to 0.0 for peso as we need the total portfolio value to calculate it
            peso = 0.0
            
            items.append(PositionUIRepresentationDTO(
                ticker=r['ticker'],
                classe_ativo=r.get('classe_ativo'),
                observacao=r.get('observacao'),
                data_snapshot=str(r.get('data_snapshot')) if r.get('data_snapshot') else None,
                quantidade=r.get('quantidade') or 0.0,
                valor_investido=valor_investido,
                valor_atual=valor_atual,
                ganho=ganho,
                peso=peso
            ))
        
        return PaginatedResponse(
            items=items,
            total=total,
            page=(offset // limit) + 1 if limit > 0 else 1,
            page_size=limit
        )

class DividendService:
    def __init__(self, session: Session):
        self.repository = DividendRepository(session)

    def list_dividends(self, limit: int = 50, offset: int = 0) -> PaginatedResponse:
        raw_items = self.repository.list_dividends(limit, offset)
        total = self.repository.count_dividends()
        
        items = [DividendUIRepresentationDTO(**item) for item in raw_items]
        
        return PaginatedResponse(
            items=items,
            total=total,
            page=(offset // limit) + 1 if limit > 0 else 1,
            page_size=limit
        )
