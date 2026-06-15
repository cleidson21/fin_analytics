import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.api.deps import require_admin
from app.api.services.governance_service import GovernanceService

router = APIRouter(dependencies=[Depends(require_admin)])
service = GovernanceService()

class PromptVersionCreate(BaseModel):
    name: str
    version: int
    content: str
    notes: Optional[str] = None

class PromptVersionResponse(BaseModel):
    id: str
    name: str
    version: int
    content: str
    active: bool
    created_at: datetime
    notes: Optional[str]


@router.post("/seed")
def seed_prompts():
    """Alimenta a base de dados com as seeds iniciais de prompts (Sprint 0.5)"""
    seeds = [
        {"name": "prompt_pix", "version": 1, "content": "Você é um assistente...", "notes": "Seed inicial"},
        {"name": "prompt_cartao", "version": 1, "content": "Você é um assistente...", "notes": "Seed inicial"},
        {"name": "prompt_fatura", "version": 1, "content": "Você é um assistente...", "notes": "Seed inicial"},
        {"name": "prompt_extrato", "version": 1, "content": "Você é um assistente...", "notes": "Seed inicial"},
    ]
    
    for seed in seeds:
        exists = service.get_prompt_version_exists(seed["name"], seed["version"])
        if not exists:
            service.insert_prompt_version(
                uuid.uuid4().hex, seed["name"], seed["version"], seed["content"], 1, seed["notes"]
            )
    return {"status": "SUCCESS", "message": "Seeds criadas com sucesso"}

@router.get("", response_model=list[PromptVersionResponse])
def list_prompts(active_only: bool = False):
    return service.get_all_prompts(active_only)

@router.post("", response_model=PromptVersionResponse)
def create_prompt(prompt: PromptVersionCreate):
    prompt_id = uuid.uuid4().hex
    try:
        service.insert_prompt_version(
            prompt_id, prompt.name, prompt.version, prompt.content, 0, prompt.notes
        )
        return service.get_prompt_by_id(prompt_id)
    except Exception as e:
        if "UNIQUE" in str(e):
            raise HTTPException(status_code=400, detail="Esta versão para este nome de prompt já existe.")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{prompt_id}", response_model=PromptVersionResponse)
def get_prompt(prompt_id: str):
    row = service.get_prompt_by_id(prompt_id)
    if not row:
        raise HTTPException(status_code=404, detail="Prompt não encontrado")
    return row

@router.post("/{prompt_id}/activate")
def activate_prompt(prompt_id: str):
    success = service.activate_prompt_version(prompt_id)
    if not success:
        raise HTTPException(status_code=404, detail="Prompt não encontrado")
    return {"status": "SUCCESS"}
