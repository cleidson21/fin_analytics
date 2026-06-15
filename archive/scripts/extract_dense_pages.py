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
    
    if not filename.startswith('src/app') and not filename.startswith('src/components/dashboard'):
        continue
        
    print(f"\n[{filename}]")
    for line in lines[1:]:
        line_s = line.strip()
        if line_s.startswith('import') and ('use' in line_s or 'store' in line_s or 'api' in line_s):
            print(f"  {line_s}")
        elif 'use' in line_s and '(' in line_s and '=' in line_s:
            print(f"  {line_s}")
        elif line_s.startswith('<') and not line_s.startswith('</'):
            tag = line_s.split(' ')[0].split('>')[0].split('/')[0].strip('<')
            if tag and tag[0].isupper():
                print(f"  JSX: <{tag}>")
