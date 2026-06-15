import re

def inject_observability(filepath, method_names):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Ensure import is at the top
    if 'from app.core.observability import transaction_scope' not in content:
        content = 'from app.core.observability import transaction_scope, query_scope\n' + content

    for m in method_names:
        # We find the definition
        pattern = r'(    def ' + m + r'\(.*?\)(?: -> .*)?:)(.*?)(?=\n    def |\Z)'
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            print(f"Method {m} not found in {filepath}")
            continue
            
        old_body = match.group(2)
        
        if 'transaction_scope' in old_body:
            continue

        # Replace 'with self._get_connection() as conn:'
        new_body = re.sub(
            r'with self\._get_connection\(\) as conn:',
            f'with self._get_connection() as conn, transaction_scope(conn, "{m}"):',
            old_body
        )
        
        content = content.replace(old_body, new_body)
        print(f"Patched {m} in {filepath}")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

financial_methods = [
    'save_transaction', 'upsert_transactions', 'update_transaction', 'delete_transaction',
    'update_position', 'update_dividend', 'merge_categories', 'update_transaction_category',
    'rollback_financial_data', 'upsert_positions', 'upsert_dividends', 'upsert_portfolio_evolution'
]
inject_observability('database/financial_repository.py', financial_methods)

governance_methods = [
    'process_staging_to_transactions', 'rollback_import_run', 'insert_prompt_version',
    'upsert_rule', 'promote_all_wealth_staging', 'update_import_run_status'
]
inject_observability('database/governance_repository.py', governance_methods)
