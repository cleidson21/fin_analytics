import os
import ast
import re

base_dir = r"C:\Users\Cleidson\Pictures\fin_analytics_v2"

# 1. Check Routes
routes_dir = os.path.join(base_dir, "app", "api", "routes")
print("=== ROUTES ===")
for file in os.listdir(routes_dir):
    if file.endswith('.py') and file != '__init__.py':
        path = os.path.join(routes_dir, file)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Find @router.get('/path'), @router.post, etc
            matches = re.findall(r'@router\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]', content)
            for method, endpoint in matches:
                print(f"{method.upper()} {endpoint} -> {file}")

print("\n=== SERVICES ===")
services_dir = os.path.join(base_dir, "app", "api", "services")
for file in os.listdir(services_dir):
    if file.endswith('.py') and file != '__init__.py':
        path = os.path.join(services_dir, file)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            classes = re.findall(r'class\s+(\w+)', content)
            funcs = re.findall(r'def\s+([a-zA-Z0-9_]+)\(', content)
            print(f"{file} -> Classes: {classes}, Top Funcs: {funcs[:5]}")

print("\n=== REPOSITORIES ===")
repos = [
    os.path.join(base_dir, "database", "financial_repository.py"),
    os.path.join(base_dir, "database", "governance_repository.py")
]
for r in repos:
    if os.path.exists(r):
        with open(r, 'r', encoding='utf-8') as f:
            content = f.read()
            classes = re.findall(r'class\s+(\w+)', content)
            print(f"{os.path.basename(r)} -> {classes}")

print("\n=== SQL QUERIES ===")
# Let's search for SELECT, INSERT, UPDATE, DELETE inside triple quotes or string literals in repos
for r in repos:
    if os.path.exists(r):
        with open(r, 'r', encoding='utf-8') as f:
            content = f.read()
            queries = re.findall(r'(?i)(SELECT\s+.*?FROM\s+[\w_]+|INSERT\s+INTO\s+[\w_]+|UPDATE\s+[\w_]+|DELETE\s+FROM\s+[\w_]+)', content)
            for q in queries[:10]: # Print first few to understand usage
                clean_q = q.replace('\n', ' ')[:80]
                print(f"[{os.path.basename(r)}] {clean_q}...")

print("\n=== SCHEMAS / DTOs ===")
schemas_dir = os.path.join(base_dir, "app", "api", "schemas")
for file in os.listdir(schemas_dir):
    if file.endswith('.py') and file != '__init__.py':
        path = os.path.join(schemas_dir, file)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            classes = re.findall(r'class\s+(\w+)', content)
            print(f"{file} -> {classes}")

print("\n=== MIDDLEWARES ===")
main_py = os.path.join(base_dir, "app", "api", "main.py")
if os.path.exists(main_py):
    with open(main_py, 'r', encoding='utf-8') as f:
        content = f.read()
        if 'CORSMiddleware' in content: print("CORSMiddleware used.")
        middlewares = re.findall(r'@app\.middleware\([\'"](\w+)[\'"]\)\s+async\s+def\s+(\w+)', content)
        for m, func in middlewares:
            print(f"Middleware {m}: {func}")
        adds = re.findall(r'app\.add_middleware\((.*?)\)', content)
        for a in adds:
            print(f"app.add_middleware({a[:30]}...)")

print("\n=== AUTH ===")
auth_files = [
    os.path.join(base_dir, "app", "api", "deps.py"),
    os.path.join(base_dir, "app", "api", "routes", "auth.py"),
    os.path.join(base_dir, "app", "api", "services", "auth_service.py")
]
for a in auth_files:
    if os.path.exists(a):
        print(f"Found Auth component: {os.path.basename(a)}")

print("\n=== ETL ===")
etl_dir = os.path.join(base_dir, "etl")
for file in os.listdir(etl_dir):
    if file.endswith('.py') and file != '__init__.py':
        print(f"ETL: {file}")
normalizers = os.path.join(etl_dir, "normalizers")
if os.path.exists(normalizers):
    for file in os.listdir(normalizers):
        if file.endswith('.py') and file != '__init__.py':
             print(f"ETL Normalizer: {file}")

print("\n=== IA ===")
ia_files = [
    os.path.join(base_dir, "app", "api", "routes", "prompts.py"),
    os.path.join(base_dir, "app", "api", "routes", "learning.py"),
    os.path.join(base_dir, "services", "categorizer.py")
]
for ia in ia_files:
    if os.path.exists(ia):
        print(f"Found IA component: {os.path.basename(ia)}")
