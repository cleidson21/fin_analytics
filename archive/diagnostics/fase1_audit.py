import os
import re

def audit_frontend():
    print("=== FRONTEND INVENTORY ===")
    frontend_dir = 'frontend/src/app'
    if not os.path.exists(frontend_dir):
        print(f"Directory {frontend_dir} not found.")
        return

    for root, dirs, files in os.walk(frontend_dir):
        for file in files:
            if file == 'page.tsx':
                path = os.path.join(root, file)
                content = open(path, 'r', encoding='utf-8').read()
                
                # APIs
                apis = re.findall(r'(?:fetchFromAPI|fetch|axios\.(?:get|post|put|delete))\([\'\"\`](.*?)[\'\\"\`]', content)
                
                # Components (just a heuristic, capitalized tags)
                components = set(re.findall(r'<([A-Z][a-zA-Z0-9_]+)', content))
                
                # Hooks
                hooks = set(re.findall(r'(use[A-Z][a-zA-Z0-9_]+)', content))
                
                route = path.replace('frontend/src/app', '').replace('\\', '/').replace('/page.tsx', '')
                if not route: route = '/'
                
                print(f"Page: {route}")
                print(f"  File: {path}")
                print(f"  APIs: {set(apis)}")
                print(f"  Hooks: {hooks}")
                print(f"  Components: {components}")
                print("-" * 40)

def audit_endpoints():
    print("=== ENDPOINTS INVENTORY ===")
    api_dir = 'app/api/routes'
    if not os.path.exists(api_dir):
        print(f"Directory {api_dir} not found.")
        return

    for root, dirs, files in os.walk(api_dir):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                content = open(path, 'r', encoding='utf-8').read()
                
                endpoints = re.findall(r'@router\.(get|post|put|delete)\([\'\"\`](.*?)[\'\\"\`]', content)
                services = set(re.findall(r'([A-Z][a-zA-Z0-9_]+Service)\(', content))
                repos = set(re.findall(r'([A-Z][a-zA-Z0-9_]+Repository|DatabaseManager)', content))
                
                print(f"Router: {file}")
                for method, route in endpoints:
                    print(f"  Endpoint: [{method.upper()}] {route}")
                print(f"  Services used: {services}")
                print(f"  Repos used: {repos}")
                print("-" * 40)

def audit_services():
    print("=== SERVICES INVENTORY ===")
    svc_dir = 'app/services'
    if not os.path.exists(svc_dir):
        print(f"Directory {svc_dir} not found.")
        return

    for root, dirs, files in os.walk(svc_dir):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                content = open(path, 'r', encoding='utf-8').read()
                classes = re.findall(r'class ([A-Z][a-zA-Z0-9_]+)', content)
                methods = re.findall(r'def ([a-zA-Z0-9_]+)\(', content)
                
                print(f"Service File: {file}")
                print(f"  Classes: {classes}")
                print(f"  Methods: {[m for m in methods if not m.startswith('__')]}")
                print("-" * 40)

def audit_repository():
    print("=== REPOSITORY INVENTORY ===")
    repo_path = 'database/repository.py'
    if not os.path.exists(repo_path):
        print(f"File {repo_path} not found.")
        return
        
    content = open(repo_path, 'r', encoding='utf-8').read()
    methods = re.findall(r'def ([a-zA-Z0-9_]+)\(', content)
    # Simple heuristic to find tables used
    tables = set(re.findall(r'(?:FROM|JOIN|INTO|UPDATE|TABLE)\s+([a-z_]+)', content, re.IGNORECASE))
    
    print(f"Repository Methods: {[m for m in methods if not m.startswith('__')]}")
    print(f"Tables referenced: {tables}")
    print("-" * 40)

if __name__ == '__main__':
    audit_frontend()
    audit_endpoints()
    audit_services()
    audit_repository()
