import os
import re

in_path = r'C:\Users\Cleidson\Pictures\fin_analytics_v2\dependency_data.txt'

with open(in_path, 'r', encoding='utf-8') as f:
    content = f.read()

files = content.split('==== ')
for file_block in files:
    if not file_block.strip(): continue
    lines = file_block.split('\n')
    filename = lines[0].replace(' ====', '').strip()
    
    print(f"\n[{filename}]")
    for line in lines[1:]:
        line_s = line.strip()
        # Keep imports that might indicate hooks/stores
        if line_s.startswith('import') and ('use' in line_s or 'store' in line_s or 'api' in line_s):
            print(f"  {line_s}")
        # Keep component/function declarations
        elif line_s.startswith('export ') or line_s.startswith('const ') and '=>' in line_s:
            if 'export' in line_s or ('const' in line_s and '=>' in line_s):
                print(f"  {line_s}")
        # Keep hook calls
        elif 'use' in line_s and '(' in line_s and '=' in line_s:
            print(f"  {line_s}")
        # Keep fetch/api calls
        elif 'fetch' in line_s or 'api.' in line_s:
            print(f"  {line_s}")
        # Keep JSX returns (just the tags)
        elif line_s.startswith('<') and not line_s.startswith('</'):
            tag = line_s.split(' ')[0].split('>')[0].strip('<')
            if tag and tag[0].isupper():
                print(f"  JSX: <{tag}>")
        # Keep type definitions
        elif line_s.startswith('export interface') or line_s.startswith('export type'):
             print(f"  {line_s}")
