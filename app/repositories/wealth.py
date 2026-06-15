from app.repositories.base import BaseRepository
from app.models.wealth import Position, Dividend, PortfolioEvolution, Benchmark
from sqlalchemy.orm import Session
from typing import Any, Optional

class PositionRepository(BaseRepository[Position]):
    def __init__(self):
        super().__init__(Position)

    # Note: Position uses composite primary key (ticker, data_snapshot)
    def get(self, db: Session, id: Any) -> Optional[Position]:
        # 'id' is expected to be a tuple (ticker, data_snapshot)
        ticker, data_snapshot = id
        return db.query(self.model).filter(
            self.model.ticker == ticker,
            self.model.data_snapshot == data_snapshot
        ).first()

class DividendRepository(BaseRepository[Dividend]):
    def __init__(self):
        super().__init__(Dividend)

    def get(self, db: Session, id: Any) -> Optional[Dividend]:
        return db.query(self.model).filter(self.model.id_economico == id).first()

class PortfolioEvolutionRepository(BaseRepository[PortfolioEvolution]):
    def __init__(self):
        super().__init__(PortfolioEvolution)

class BenchmarkRepository(BaseRepository[Benchmark]):
    def __init__(self):
        super().__init__(Benchmark)
