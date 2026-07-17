from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class PluginMetadata(BaseModel):
    plugin_id: str
    name: str
    version: str
    description: str
    author: str
    enabled: bool = True
    entrypoint: str
    dependencies: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PluginStatus(BaseModel):
    loaded: bool = False
    healthy: bool = False
    last_execution: Optional[datetime] = None
    execution_time_ms: int = 0
    errors: List[str] = Field(default_factory=list)
