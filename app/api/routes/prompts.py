import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.api.deps import require_admin
from database.repository import DatabaseManager

router = APIRouter(dependencies=[Depends(require_admin)])
repository = DatabaseManager()

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
    created_at: str
    notes: Optional[str]

@router.post("/seed")
def seed_prompts():
    """Alimenta a base de dados com as seeds iniciais de prompts (Sprint 0.5)"""
    seeds = [
        {"name": "prompt_pix", "version": 1, "content": "Você é um assistente... Extraia os dados do PIX...", "notes": "Seed inicial"},
        {"name": "prompt_cartao", "version": 1, "content": "Você é um assistente... Extraia os dados da compra no cartão...", "notes": "Seed inicial"},
        {"name": "prompt_fatura", "version": 1, "content": "Você é um assistente... Extraia os dados da fatura...", "notes": "Seed inicial"},
        {"name": "prompt_extrato", "version": 1, "content": "Você é um assistente... Extraia os dados do extrato geral...", "notes": "Seed inicial"},
    ]
    
    with repository._get_connection() as conn:
        cursor = conn.cursor()
        for seed in seeds:
            # Verifica se já existe
            exists = cursor.execute("SELECT 1 FROM prompt_versions WHERE name = ? AND version = ?", (seed["name"], seed["version"])).fetchone()
            if not exists:
                cursor.execute(
                    """
                    INSERT INTO prompt_versions (id, name, version, content, active, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (uuid.uuid4().hex, seed["name"], seed["version"], seed["content"], 1, seed["notes"])
                )
        conn.commit()
    
    return {"status": "SUCCESS", "message": "Seeds criadas com sucesso"}

@router.get("", response_model=list[PromptVersionResponse])
def list_prompts(active_only: bool = False):
    with repository._get_connection() as conn:
        query = "SELECT * FROM prompt_versions"
        if active_only:
            query += " WHERE active = 1"
        query += " ORDER BY name, version DESC"
        
        rows = conn.execute(query).fetchall()
        
    return [dict(r) for r in rows]

@router.post("", response_model=PromptVersionResponse)
def create_prompt(prompt: PromptVersionCreate):
    prompt_id = uuid.uuid4().hex
    try:
        with repository._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO prompt_versions (id, name, version, content, active, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (prompt_id, prompt.name, prompt.version, prompt.content, 0, prompt.notes)
            )
            conn.commit()
            
            row = cursor.execute("SELECT * FROM prompt_versions WHERE id = ?", (prompt_id,)).fetchone()
            return dict(row)
    except Exception as e:
        if "UNIQUE" in str(e):
            raise HTTPException(status_code=400, detail="Esta versão para este nome de prompt já existe.")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{prompt_id}", response_model=PromptVersionResponse)
def get_prompt(prompt_id: str):
    with repository._get_connection() as conn:
        row = conn.execute("SELECT * FROM prompt_versions WHERE id = ?", (prompt_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Prompt não encontrado")
    return dict(row)

@router.post("/{prompt_id}/activate")
def activate_prompt(prompt_id: str):
    with repository._get_connection() as conn:
        cursor = conn.cursor()
        
        row = cursor.execute("SELECT name FROM prompt_versions WHERE id = ?", (prompt_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Prompt não encontrado")
            
        prompt_name = row["name"]
        
        # Desativa todos com mesmo nome
        cursor.execute("UPDATE prompt_versions SET active = 0 WHERE name = ?", (prompt_name,))
        # Ativa o alvo
        cursor.execute("UPDATE prompt_versions SET active = 1 WHERE id = ?", (prompt_id,))
        
        conn.commit()
    
    return {"status": "SUCCESS"}
