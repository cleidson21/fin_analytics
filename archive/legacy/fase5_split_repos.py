import ast
import os

fin_methods = [
    "__init__", "_get_connection", "_init_db", "_apply_transaction_migrations",
    "upsert_transactions", "upsert_positions", "upsert_dividends", "upsert_portfolio_evolution",
    "get_user_by_username", "create_user", "vacuum_database", "analyze_database", "_dict_factory",
    "update_transaction", "update_position", "update_dividend", "merge_categories"
]

gov_methods = [
    "__init__", "_get_connection",
    "register_etl_run", "update_etl_run_metrics", "create_import_run", "create_import_artifact",
    "update_import_run_status", "update_import_run_metrics", "insert_staging_items",
    "process_staging_to_transactions", "insert_wealth_staging_items", "mark_staging_conflicts",
    "rollback_import_run", "lock_import_run_for_confirmation", "promote_all_wealth_staging",
    "insert_raw_events", "create_event_links", "get_active_hints", "promote_raw_events",
    "create_audit_log", "get_orphans_count", "update_event_link_status", "get_run_ids_for_link",
    "get_active_rules", "upsert_rule", "record_rule_feedback", "get_learning_metrics",
    "get_rules_audit", "get_top_rules", "get_problematic_rules"
]

def strip_methods(filepath, keep_methods, db_path_constant, class_name):
    with open(filepath, 'r', encoding='utf-8') as f:
        code = f.read()
    
    # We must replace DATABASE_PATH with db_path_constant in imports
    code = code.replace("from database.config import DATABASE_PATH", f"from database.config import {db_path_constant} as DATABASE_PATH")
    
    tree = ast.parse(code)
    
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == 'DatabaseManager':
            node.name = class_name
            new_body = []
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    if child.name in keep_methods:
                        new_body.append(child)
                else:
                    new_body.append(child)
            node.body = new_body
            
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(ast.unparse(tree))

def rewrite_adapter():
    code = """import logging
from typing import Dict, List, Optional, Any
from datetime import date
from database.financial_repository import FinancialRepository
from database.governance_repository import GovernanceRepository

logger = logging.getLogger(__name__)

class DatabaseManager:
    \"\"\"
    [DEPRECATED] Adapter de Compatibilidade para a Fase 5.
    Encaminha as chamadas para o repositório correto.
    \"\"\"
    def __init__(self):
        self.financial = FinancialRepository()
        self.governance = GovernanceRepository()

"""
    # Create wrapper methods automatically based on all existing methods
    fin_set = set(fin_methods) - {"__init__", "_get_connection", "_init_db", "_apply_transaction_migrations", "_dict_factory"}
    gov_set = set(gov_methods) - {"__init__", "_get_connection"}
    
    # For kwargs simply use *args, **kwargs
    for m in fin_set:
        code += f"    def {m}(self, *args, **kwargs):\n        return self.financial.{m}(*args, **kwargs)\n\n"
    for m in gov_set:
        code += f"    def {m}(self, *args, **kwargs):\n        return self.governance.{m}(*args, **kwargs)\n\n"
        
    with open('database/repository.py', 'w', encoding='utf-8') as f:
        f.write(code)

if __name__ == "__main__":
    strip_methods('database/financial_repository.py', fin_methods, "DATABASE_PATH", "FinancialRepository")
    strip_methods('database/governance_repository.py', gov_methods, "GOVERNANCE_DB_PATH", "GovernanceRepository")
    rewrite_adapter()
