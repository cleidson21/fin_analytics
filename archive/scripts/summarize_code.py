import os
import re

src_dir = r"C:\Users\Cleidson\Pictures\fin_analytics_v2\frontend\src"

def analyze_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    rel_path = os.path.relpath(filepath, src_dir).replace('\\', '/')
    
    # Very basic regex heuristics
    exports = re.findall(r'export\s+(?:default\s+)?(?:const|function|class|interface|type)\s+([A-Za-z0-9_]+)', content)
    hooks = re.findall(r'\b(use[A-Z][A-Za-z0-9_]*)\b', content)
    hooks = list(set(hooks))
    
    # Try to find JSX tags
    jsx_tags = re.findall(r'<([A-Z][A-Za-z0-9_]+)', content)
    jsx_tags = list(set(jsx_tags))
    
    # Try to find what it returns (the JSX part)
    # Just grab some keywords that indicate functionality
    keywords = ['Table', 'Chart', 'Modal', 'Dialog', 'Card', 'Button', 'Input', 'Select', 'Form']
    found_keywords = [kw for kw in keywords if kw.lower() in content.lower()]
    
    return {
        'path': rel_path,
        'exports': exports,
        'hooks': hooks,
        'jsx': jsx_tags,
        'keywords': found_keywords,
        'lines': len(content.split('\n'))
    }

print("=== START OF SUMMARY ===")
for root, dirs, files in os.walk(src_dir):
    for file in files:
        if file.endswith('.ts') or file.endswith('.tsx'):
            if file == 'all_files.txt': continue
            filepath = os.path.join(root, file)
            info = analyze_file(filepath)
            print(f"File: {info['path']}")
            print(f"  Exports: {', '.join(info['exports'])}")
            print(f"  Hooks used: {', '.join(info['hooks'])}")
            print(f"  JSX Components: {', '.join(info['jsx'])}")
            print(f"  Keywords found: {', '.join(info['keywords'])}")
            print(f"  Lines: {info['lines']}")
            print("-" * 40)
print("=== END OF SUMMARY ===")
