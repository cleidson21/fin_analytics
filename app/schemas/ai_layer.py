from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RuleBase(BaseModel):
    rule_type: str
    pattern: str
    action: str

class RuleResponse(RuleBase):
    id: str
    status: str
    class Config:
        from_attributes = True

class PromptVersionBase(BaseModel):
    name: str
    version: int
    content: str

class PromptVersionResponse(PromptVersionBase):
    id: str
    class Config:
        from_attributes = True

class AiRunBase(BaseModel):
    model: str
    input_text: str

class AiRunResponse(AiRunBase):
    id: str
    status: str
    class Config:
        from_attributes = True
