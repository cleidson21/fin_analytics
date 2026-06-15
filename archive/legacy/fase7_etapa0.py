import os
import re

terms = [
    'DatabaseManager', 'FinancialQueries', 'rules', 'audit_log', 'import_runs', 'import_artifacts',
    'prompt_versions', 'ai_runs', 'staging_imports', 'staging_positions', 'staging_dividends',
    'staging_portfolio_evolution', 'raw_events', 'event_links', 'vw_rules_training_dataset'
]

ignores = ['database/queries.py', 'database/repository.py', 'archive', 'diagnostics', 'reports']

found = []
for root, dirs, files in os.walk('.'):
    # Skip standard ignores
    if '.git' in root or '.venv' in root or '__pycache__' in root or '.gemini' in root or 'node_modules' in root:
        continue
    
    for file in files:
        if not file.endswith('.py') and not file.endswith('.sql') and not file.endswith('.md'):
            continue
            
        path = os.path.join(root, file).replace('\\', '/')
        if any(ig in path for ig in ignores):
            continue
            
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for i, line in enumerate(f):
                for term in terms:
                    if term in line:
                        # Classify
                        is_comment = line.strip().startswith('#') or line.strip().startswith('--')
                        is_doc = file.endswith('.md') or ('\"\"\"' in line)
                        is_archive = 'archive' in path or file.startswith('fase')
                        
                        classification = 'ativo'
                        if is_comment: classification = 'comentário'
                        elif is_doc: classification = 'documentação'
                        elif is_archive: classification = 'script arquivado'
                        
                        found.append({'file': path, 'line': i+1, 'term': term, 'class': classification})

active_issues = [f for f in found if f['class'] == 'ativo' and f['file'].endswith('.py') and not f['file'].endswith('seed_admin.py')]
for iss in active_issues:
    print(f"{iss['file']}:{iss['line']} - {iss['term']} [{iss['class']}]")

if not active_issues:
    print('ETAPA 0 CLEAN')
