import os
import re

def audit_services_2():
    print("=== SERVICES ===")
    svc_dir = 'services'
    if os.path.exists(svc_dir):
        for root, dirs, files in os.walk(svc_dir):
            for file in files:
                if file.endswith('.py'):
                    path = os.path.join(root, file)
                    content = open(path, 'r', encoding='utf-8').read()
                    classes = re.findall(r'class ([A-Z][a-zA-Z0-9_]+)', content)
                    methods = re.findall(r'def ([a-zA-Z0-9_]+)\(', content)
                    print(f"Service File: {file} | Classes: {classes}")
                    print(f"Methods: {[m for m in methods if not m.startswith('__')]}")

def audit_queries():
    print("=== QUERIES ===")
    q_dir = 'database/queries.py'
    if os.path.exists(q_dir):
        content = open(q_dir, 'r', encoding='utf-8').read()
        classes = re.findall(r'class ([A-Z][a-zA-Z0-9_]+)', content)
        methods = re.findall(r'def ([a-zA-Z0-9_]+)\(', content)
        print(f"Classes: {classes}")
        print(f"Methods: {[m for m in methods if not m.startswith('__')]}")

def audit_ai():
    print("=== PROMPT VERSIONS & AI ===")
    for root, dirs, files in os.walk('app'):
        for file in files:
            if file.endswith('.py'):
                content = open(os.path.join(root, file), 'r', encoding='utf-8').read()
                if 'ai_runs' in content or 'prompt_versions' in content or 'Gemini' in content:
                    print(f"AI usage found in: {file}")

if __name__ == '__main__':
    audit_services_2()
    audit_queries()
    audit_ai()
