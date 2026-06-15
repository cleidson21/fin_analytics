import os
import re

base_dir = r"C:\Users\Cleidson\Pictures\fin_analytics_v2"
frontend_dir = os.path.join(base_dir, "frontend", "src")
backend_dir = os.path.join(base_dir, "app")
database_dir = os.path.join(base_dir, "database")

# 1. Frontend Files
pages = []
hooks = []
stores = []

for root, _, files in os.walk(frontend_dir):
    for f in files:
        path = os.path.join(root, f)
        rel_path = os.path.relpath(path, frontend_dir).replace('\\', '/')
        if f == 'page.tsx':
            pages.append(rel_path)
        elif 'hooks' in rel_path.split('/'):
            hooks.append(rel_path)
        elif 'stores' in rel_path.split('/'):
            stores.append(rel_path)

# Collect all frontend content
frontend_contents = ""
for root, _, files in os.walk(frontend_dir):
    for f in files:
        if f.endswith(('.ts', '.tsx')):
            with open(os.path.join(root, f), 'r', encoding='utf-8', errors='ignore') as file:
                frontend_contents += file.read() + "\n"

# Check orphan hooks
orphan_hooks = []
for h in hooks:
    basename = os.path.splitext(os.path.basename(h))[0]
    # Check if used (count occurrences). 1 occurrence is its own definition.
    count = frontend_contents.count(basename)
    if count <= 1:
        orphan_hooks.append(h)

# Check orphan stores
orphan_stores = []
for s in stores:
    basename = os.path.splitext(os.path.basename(s))[0]
    count = frontend_contents.count(basename)
    if count <= 1:
        orphan_stores.append(s)

# Check orphan pages (no <Link href="..."> or router.push)
orphan_pages = []
for p in pages:
    route = p.replace('/page.tsx', '')
    if route == 'app':
        continue # root page is never orphan
    route = route.replace('app', '') # e.g. /wealth, /transactions
    # count references
    if route == '':
        continue
    if route not in frontend_contents and f"{route}/" not in frontend_contents:
        # dynamic routes check
        if '[' in route:
            continue
        orphan_pages.append(p)

# 2. Backend Files
services = []
for root, _, files in os.walk(os.path.join(backend_dir, "api", "services")):
    for f in files:
        if f.endswith('.py') and f != '__init__.py':
            services.append(f)

backend_contents = ""
for root, _, files in os.walk(base_dir):
    if 'archive' in root or '.venv' in root or 'frontend' in root:
        continue
    for f in files:
        if f.endswith('.py'):
            with open(os.path.join(root, f), 'r', encoding='utf-8', errors='ignore') as file:
                backend_contents += file.read() + "\n"

orphan_services = []
for s in services:
    basename = os.path.splitext(s)[0]
    # In python, imported as `from app.api.services.basename import ...`
    count = backend_contents.count(basename)
    if count <= 1: # only its own file
        orphan_services.append(s)

# Endpoints
endpoints = []
for root, _, files in os.walk(os.path.join(backend_dir, "api", "routes")):
    for f in files:
        if f.endswith('.py') and f != '__init__.py':
            with open(os.path.join(root, f), 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                matches = re.findall(r'@router\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]', content)
                for method, endpoint in matches:
                    # Clean up endpoint formatting
                    base_end = endpoint.split('{')[0].strip('/')
                    endpoints.append((f, method, endpoint, base_end))

orphan_endpoints = []
for file, method, endpoint, base_end in endpoints:
    if base_end == "":
        continue
    # Check if base_end is in frontend_contents
    if base_end not in frontend_contents:
        orphan_endpoints.append(f"{method.upper()} {endpoint} ({file})")

# Tables
tables = []
schema_path = os.path.join(database_dir, "schema.sql")
if os.path.exists(schema_path):
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_content = f.read()
        tables = re.findall(r'CREATE TABLE IF NOT EXISTS\s+(\w+)', schema_content)

orphan_tables = []
for t in tables:
    # Check if queried in backend_contents
    if t not in backend_contents:
        orphan_tables.append(t)

print("=== DEAD CODE REPORT ===")
print("Páginas Órfãs:", orphan_pages)
print("Hooks Órfãos:", orphan_hooks)
print("Stores Órfãos:", orphan_stores)
print("Serviços Órfãos:", orphan_services)
print("Endpoints Órfãos:", orphan_endpoints)
print("Tabelas Órfãs:", orphan_tables)
