from app.repositories.base import BaseRepository
from app.models.ai_layer import Rule, PromptVersion, AiRun

class RuleRepository(BaseRepository[Rule]):
    def __init__(self):
        super().__init__(Rule)

class PromptVersionRepository(BaseRepository[PromptVersion]):
    def __init__(self):
        super().__init__(PromptVersion)

class AiRunRepository(BaseRepository[AiRun]):
    def __init__(self):
        super().__init__(AiRun)
