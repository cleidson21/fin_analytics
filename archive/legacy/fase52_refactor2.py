import ast

def extract_methods(filepath, method_names):
    with open(filepath, 'r', encoding='utf-8') as f:
        code = f.read()
    tree = ast.parse(code)
    extracted = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name in method_names:
                    extracted.append(ast.unparse(child))
    return extracted

gov_query_methods = [
    'get_wealth_staging_items', 'get_import_runs', 'get_import_run_by_id',
    'get_audit_log_by_id', 'get_audit_logs', 'get_import_status', 'get_reconciliation_inbox'
]
fin_query_methods = [
    'get_admin_positions', 'get_dashboard_metrics', 'get_quarantine_transactions',
    'get_admin_dividends', 'get_admin_categories'
]

gov_methods_code = extract_methods('database/queries.py', gov_query_methods)
fin_methods_code = extract_methods('database/queries.py', fin_query_methods)

# Append to repos
def append_to_file(filepath, codes):
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write('\n')
        for c in codes:
            # Need to indent properly if not part of a class, but AST unparse of a class method
            # retains its indentation? No, unparse removes the class context, so it unparses as top-level function.
            # We must indent it.
            indented = '\n'.join('    ' + line for line in c.split('\n'))
            f.write(indented + '\n\n')

append_to_file('database/governance_repository.py', gov_methods_code)
append_to_file('database/financial_repository.py', fin_methods_code)

# Add to adapter
adapter_code = ""
for m in gov_query_methods:
    adapter_code += f"    def {m}(self, *args, **kwargs):\n        return self.governance.{m}(*args, **kwargs)\n\n"
for m in fin_query_methods:
    adapter_code += f"    def {m}(self, *args, **kwargs):\n        return self.financial.{m}(*args, **kwargs)\n\n"

with open('database/repository.py', 'a', encoding='utf-8') as f:
    f.write(adapter_code)

# Now refactor governance.py
with open('app/api/routes/governance.py', 'r', encoding='utf-8') as f:
    gov_py = f.read()

# Replace imports
gov_py = gov_py.replace("from database.repository import DatabaseManager\nfrom database.queries import FinancialQueries",
"""from database.financial_repository import FinancialRepository
from database.governance_repository import GovernanceRepository""")
gov_py = gov_py.replace("queries = FinancialQueries()\nrepository = DatabaseManager()",
"""fin_repo = FinancialRepository()
gov_repo = GovernanceRepository()""")

# Replace repository.
# gov_methods are in GovernanceRepository
gov_repo_methods = ['update_event_link_status', 'update_import_run_metrics', 'create_event_links', 'create_import_artifact', 'mark_staging_conflicts', 'lock_import_run_for_confirmation', 'create_import_run', 'insert_staging_items', 'promote_raw_events', 'get_active_hints', 'get_orphans_count', 'promote_all_wealth_staging', 'process_staging_to_transactions', 'insert_wealth_staging_items', 'get_run_ids_for_link', 'update_import_run_status', 'insert_raw_events', 'get_wealth_staging_items', 'get_import_runs', 'get_import_run_by_id', 'get_audit_log_by_id', 'get_audit_logs', 'get_import_status', 'get_reconciliation_inbox']

fin_repo_methods = ['update_transaction', 'merge_categories', 'update_position', 'update_dividend', 'get_admin_positions', 'get_dashboard_metrics', 'get_quarantine_transactions', 'get_admin_dividends', 'get_admin_categories']

for m in gov_repo_methods:
    gov_py = gov_py.replace(f"repository.{m}", f"gov_repo.{m}")
    gov_py = gov_py.replace(f"queries.{m}", f"gov_repo.{m}")
for m in fin_repo_methods:
    gov_py = gov_py.replace(f"repository.{m}", f"fin_repo.{m}")
    gov_py = gov_py.replace(f"queries.{m}", f"fin_repo.{m}")

# Fix direct sqlite3 connections in governance.py
# Example: with repository._get_connection() as conn:
# If it's updating import_runs, it should be gov_repo
# If it's reading event_links, it's gov_repo.
# We'll replace repository._get_connection with gov_repo._get_connection, which is mostly safe for governance.py since most direct SQL there is for imports.
gov_py = gov_py.replace("repository._get_connection", "gov_repo._get_connection")

with open('app/api/routes/governance.py', 'w', encoding='utf-8') as f:
    f.write(gov_py)

print("Gov and Fin repos updated with queries. governance.py refactored.")
