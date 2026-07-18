import re

with open('backend/domains/governance/router.py', 'r', encoding='utf-8') as f:
    content = f.read()

import_stmt = 'from backend.domains.identity.router import get_current_user\n'
if 'get_current_user' not in content:
    content = content.replace('from sqlalchemy.orm import Session', 'from sqlalchemy.orm import Session\n' + import_stmt)

def inject_auth(match):
    # match.group(1) is the function definition up to the first parameter
    # match.group(2) is the rest of the parameters
    sig = match.group(0)
    if 'get_current_user' in sig:
        return sig
    
    if sig.endswith('():'):
        return sig[:-2] + 'current_user: Dict[str, Any] = Depends(get_current_user)): '
    
    # Otherwise, it has parameters. Inject it before the closing parenthesis.
    # A bit tricky. Let's do simple replacements.
    return sig

replacements = [
    ('def get_governance_dashboard(db: Session = Depends(get_db)):', 'def get_governance_dashboard(db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user)):'),
    ('def list_imports(limit: int = 10, offset: int = 0, db: Session = Depends(get_db)):', 'def list_imports(limit: int = 10, offset: int = 0, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user)):'),
    ('def get_import_run(run_id: str, db: Session = Depends(get_db)):', 'def get_import_run(run_id: str, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user)):'),
    ('def get_staging_items(run_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:', 'def get_staging_items(run_id: str, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:'),
    ('def confirm_import_run(run_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:', 'def confirm_import_run(run_id: str, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:'),
    ('def rollback_import_run(run_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:', 'def rollback_import_run(run_id: str, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:'),
    ('def get_db_summary() -> Dict[str, Any]:', 'def get_db_summary(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:'),
    ('def get_db_health() -> Dict[str, Any]:', 'def get_db_health(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:'),
    ('def get_db_tables() -> List[Dict[str, Any]]:', 'def get_db_tables(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:'),
    ('def get_db_integrity() -> Dict[str, Any]:', 'def get_db_integrity(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:'),
    ('def list_audit(status_filter: str = "ALL") -> List[Dict[str, Any]]:', 'def list_audit(status_filter: str = "ALL", current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:'),
    ('def list_rollbacks() -> List[Dict[str, Any]]:', 'def list_rollbacks(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:'),
    ('def list_positions(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):', 'def list_positions(limit: int = 50, offset: int = 0, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user)):'),
    ('def list_categories(limit: int = 50, offset: int = 0) -> Dict[str, Any]:', 'def list_categories(limit: int = 50, offset: int = 0, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:'),
    ('def list_dividends(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):', 'def list_dividends(limit: int = 50, offset: int = 0, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user)):'),
    ('async def upload_import(\n    source_type: str = Form(...),', 'async def upload_import(\n    current_user: Dict[str, Any] = Depends(get_current_user),\n    source_type: str = Form(...),')
]

for old, new in replacements:
    content = content.replace(old, new)

with open('backend/domains/governance/router.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
