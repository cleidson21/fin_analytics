import os
import re

router_path = 'backend/domains/investments/router.py'
test_path = 'backend/tests/e2e/test_api_endpoints.py'

with open(router_path, 'r', encoding='utf-8') as f:
    router_content = f.read()

# Add import for PaginatedResponse
if 'PaginatedResponse' not in router_content:
    router_content = router_content.replace('from backend.domains.investments.dto import ReconciliationResult, ImportLogDTO, PerformanceHistory, MessageResponse',
                                            'from backend.domains.investments.dto import ReconciliationResult, ImportLogDTO, PerformanceHistory, MessageResponse, PaginatedResponse')

# Function to wrap lists
def paginated(items):
    return f"PaginatedResponse(items={items}, total=len({items}), page=page, page_size=page_size)"

# Replace /positions
router_content = router_content.replace(
    'response_model=List[ValuationResult]',
    'response_model=PaginatedResponse[ValuationResult]'
).replace(
    'def get_positions(db: Session = Depends(get_db_connection)):',
    'def get_positions(db: Session = Depends(get_db_connection), page: int = 1, page_size: int = 50):'
).replace(
    "return res['valuations']",
    "return PaginatedResponse(items=res['valuations'], total=len(res['valuations']), page=page, page_size=page_size)"
)

# Replace /allocation
router_content = router_content.replace(
    'response_model=List[AssetSummary]',
    'response_model=PaginatedResponse[AssetSummary]'
).replace(
    'def get_allocation(db: Session = Depends(get_db_connection)):',
    'def get_allocation(db: Session = Depends(get_db_connection), page: int = 1, page_size: int = 50):'
).replace(
    'return get_portfolio(db).by_asset',
    'items = get_portfolio(db).by_asset\n    return PaginatedResponse(items=items, total=len(items), page=page, page_size=page_size)'
)

# Replace /institutions
router_content = router_content.replace(
    'response_model=List[InstitutionSummary]',
    'response_model=PaginatedResponse[InstitutionSummary]'
).replace(
    'def get_institutions(db: Session = Depends(get_db_connection)):',
    'def get_institutions(db: Session = Depends(get_db_connection), page: int = 1, page_size: int = 50):'
).replace(
    'return get_portfolio(db).by_institution',
    'items = get_portfolio(db).by_institution\n    return PaginatedResponse(items=items, total=len(items), page=page, page_size=page_size)'
)

# Replace /import/history
router_content = router_content.replace(
    'response_model=List[ImportLogDTO]',
    'response_model=PaginatedResponse[ImportLogDTO]'
).replace(
    'filename: str = None,\n    db: Session = Depends(get_db_connection)',
    'filename: str = None,\n    page: int = 1,\n    page_size: int = 50,\n    db: Session = Depends(get_db_connection)'
).replace(
    'return repo.list_history(db, filters)',
    'items = repo.list_history(db, filters)\n    return PaginatedResponse(items=items, total=len(items), page=page, page_size=page_size)'
)

# Replace /reconciliation
router_content = router_content.replace(
    'response_model=List[ReconciliationResult]',
    'response_model=PaginatedResponse[ReconciliationResult]'
).replace(
    'def get_reconciliation(db: Session = Depends(get_db_connection)):',
    'def get_reconciliation(db: Session = Depends(get_db_connection), page: int = 1, page_size: int = 50):'
).replace(
    'return import_app.execute_reconciliation(db)',
    'items = import_app.execute_reconciliation(db)\n    return PaginatedResponse(items=items, total=len(items), page=page, page_size=page_size)'
)

with open(router_path, 'w', encoding='utf-8') as f:
    f.write(router_content)


# Update test_api_endpoints.py
with open(test_path, 'r', encoding='utf-8') as f:
    test_content = f.read()

test_content = test_content.replace('assert isinstance(data, list)', 'assert "items" in data\n        assert isinstance(data["items"], list)')
test_content = test_content.replace('assert isinstance(resp.json(), list)', 'assert "items" in resp.json()\n    assert isinstance(resp.json()["items"], list)')

with open(test_path, 'w', encoding='utf-8') as f:
    f.write(test_content)

print('Updated pagination!')
