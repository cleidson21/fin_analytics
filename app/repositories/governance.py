from app.repositories.base import BaseRepository
from app.models.governance import (
    ImportRun, ImportArtifact, RawEvent, EventLink, AuditLog,
    StagingImport, StagingPosition, StagingDividend, StagingPortfolioEvolution
)

class ImportRunRepository(BaseRepository[ImportRun]):
    def __init__(self):
        super().__init__(ImportRun)

class ImportArtifactRepository(BaseRepository[ImportArtifact]):
    def __init__(self):
        super().__init__(ImportArtifact)

class RawEventRepository(BaseRepository[RawEvent]):
    def __init__(self):
        super().__init__(RawEvent)

class EventLinkRepository(BaseRepository[EventLink]):
    def __init__(self):
        super().__init__(EventLink)

class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self):
        super().__init__(AuditLog)

class StagingImportRepository(BaseRepository[StagingImport]):
    def __init__(self):
        super().__init__(StagingImport)

class StagingPositionRepository(BaseRepository[StagingPosition]):
    def __init__(self):
        super().__init__(StagingPosition)

class StagingDividendRepository(BaseRepository[StagingDividend]):
    def __init__(self):
        super().__init__(StagingDividend)

class StagingPortfolioEvolutionRepository(BaseRepository[StagingPortfolioEvolution]):
    def __init__(self):
        super().__init__(StagingPortfolioEvolution)
