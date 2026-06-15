import ast

# We will read prompts.py and audit.py logic and inject methods into GovernanceRepository

gov_code_additions = """
    def get_audit_runs(self, status_filter: str='ALL') -> list:
        query = 'SELECT id, file_name, source_type, started_at, status, created_by, rows_read, rows_inserted, rows_updated, rows_failed FROM import_runs'
        params = []
        if status_filter != 'ALL':
            if status_filter == 'CONFIRMED':
                query += " WHERE status = 'CONFIRMED'"
            elif status_filter == 'PENDING':
                query += " WHERE status IN ('PENDING', 'AWAITING_CONFIRMATION', 'PROCESSING_CONFIRMATION')"
            elif status_filter == 'ROLLBACK':
                query += " WHERE status = 'CANCELLED'"
            elif status_filter == 'ERROR':
                query += " WHERE status = 'FAILED'"
        query += ' ORDER BY started_at DESC'
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            return [dict(row) for row in cursor.execute(query, params).fetchall()]

    def get_audit_rollbacks(self) -> list:
        query = "SELECT id, file_name, rollback_timestamp, rollback_user, rollback_reason, started_at FROM import_runs WHERE status = 'CANCELLED' ORDER BY rollback_timestamp DESC"
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            return [dict(row) for row in cursor.execute(query).fetchall()]

    def get_prompt_version_exists(self, name: str, version: int) -> bool:
        with self._get_connection() as conn:
            row = conn.execute("SELECT 1 FROM governance_prompt_versions WHERE name = ? AND version = ?", (name, version)).fetchone()
            return bool(row)

    def insert_prompt_version(self, id: str, name: str, version: int, content: str, active: int, notes: str):
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO governance_prompt_versions (id, name, version, content, active, notes) VALUES (?, ?, ?, ?, ?, ?)",
                (id, name, version, content, active, notes)
            )
            conn.commit()

    def get_all_prompts(self, active_only: bool = False) -> list:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            query = "SELECT * FROM governance_prompt_versions"
            if active_only:
                query += " WHERE active = 1"
            query += " ORDER BY name, version DESC"
            rows = conn.execute(query).fetchall()
            return [dict(r) for r in rows]

    def get_prompt_by_id(self, prompt_id: str):
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM governance_prompt_versions WHERE id = ?", (prompt_id,)).fetchone()
            return dict(row) if row else None
            
    def activate_prompt_version(self, prompt_id: str) -> bool:
        with self._get_connection() as conn:
            row = conn.execute("SELECT name FROM governance_prompt_versions WHERE id = ?", (prompt_id,)).fetchone()
            if not row:
                return False
            prompt_name = row[0]
            conn.execute("UPDATE governance_prompt_versions SET active = 0 WHERE name = ?", (prompt_name,))
            conn.execute("UPDATE governance_prompt_versions SET active = 1 WHERE id = ?", (prompt_id,))
            conn.commit()
            return True
"""

with open('database/governance_repository.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Append to class DatabaseManager -> wait, it's GovernanceRepository
content += gov_code_additions

with open('database/governance_repository.py', 'w', encoding='utf-8') as f:
    f.write(content)

# Now refactor audit.py
audit_py = """from fastapi import APIRouter, HTTPException, Depends
from app.api.deps import require_admin
from app.api.schemas.admin import AuditRun, AuditRollback
from database.governance_repository import GovernanceRepository

router = APIRouter(dependencies=[Depends(require_admin)])
repository = GovernanceRepository()

@router.get("", response_model=list[AuditRun])
def get_audit(status_filter: str = "ALL"):
    return repository.get_audit_runs(status_filter)

@router.get("/rollbacks", response_model=list[AuditRollback])
def get_audit_rollbacks():
    return repository.get_audit_rollbacks()

@router.get("/{run_id}", response_model=AuditRun)
def get_audit_run(run_id: str):
    runs = repository.get_audit_runs("ALL")
    for r in runs:
        if r['id'] == run_id:
            return r
    raise HTTPException(status_code=404, detail="Run not found")
"""
with open('app/api/routes/audit.py', 'w', encoding='utf-8') as f:
    f.write(audit_py)

# Now refactor prompts.py
prompts_py = """import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.api.deps import require_admin
from database.governance_repository import GovernanceRepository

router = APIRouter(dependencies=[Depends(require_admin)])
repository = GovernanceRepository()

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
    \"\"\"Alimenta a base de dados com as seeds iniciais de prompts (Sprint 0.5)\"\"\"
    seeds = [
        {"name": "prompt_pix", "version": 1, "content": "Você é um assistente...", "notes": "Seed inicial"},
        {"name": "prompt_cartao", "version": 1, "content": "Você é um assistente...", "notes": "Seed inicial"},
        {"name": "prompt_fatura", "version": 1, "content": "Você é um assistente...", "notes": "Seed inicial"},
        {"name": "prompt_extrato", "version": 1, "content": "Você é um assistente...", "notes": "Seed inicial"},
    ]
    
    for seed in seeds:
        exists = repository.get_prompt_version_exists(seed["name"], seed["version"])
        if not exists:
            repository.insert_prompt_version(
                uuid.uuid4().hex, seed["name"], seed["version"], seed["content"], 1, seed["notes"]
            )
    return {"status": "SUCCESS", "message": "Seeds criadas com sucesso"}

@router.get("", response_model=list[PromptVersionResponse])
def list_prompts(active_only: bool = False):
    return repository.get_all_prompts(active_only)

@router.post("", response_model=PromptVersionResponse)
def create_prompt(prompt: PromptVersionCreate):
    prompt_id = uuid.uuid4().hex
    try:
        repository.insert_prompt_version(
            prompt_id, prompt.name, prompt.version, prompt.content, 0, prompt.notes
        )
        return repository.get_prompt_by_id(prompt_id)
    except Exception as e:
        if "UNIQUE" in str(e):
            raise HTTPException(status_code=400, detail="Esta versão para este nome de prompt já existe.")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{prompt_id}", response_model=PromptVersionResponse)
def get_prompt(prompt_id: str):
    row = repository.get_prompt_by_id(prompt_id)
    if not row:
        raise HTTPException(status_code=404, detail="Prompt não encontrado")
    return row

@router.post("/{prompt_id}/activate")
def activate_prompt(prompt_id: str):
    success = repository.activate_prompt_version(prompt_id)
    if not success:
        raise HTTPException(status_code=404, detail="Prompt não encontrado")
    return {"status": "SUCCESS"}
"""
with open('app/api/routes/prompts.py', 'w', encoding='utf-8') as f:
    f.write(prompts_py)
