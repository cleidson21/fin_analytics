import os
import re

directory = 'frontend/src'
for root, dirs, files in os.walk(directory):
    for file in files:
        if file.endswith('.tsx'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            if '<ResponsiveContainer' in content and 'minWidth=' not in content:
                content = content.replace('<ResponsiveContainer width="100%" height="100%">', '<ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>')
                content = content.replace('<ResponsiveContainer width="100%" height={300}>', '<ResponsiveContainer width="100%" height={300} minWidth={1} minHeight={1}>')
                content = content.replace('<ResponsiveContainer width="100%" height={350}>', '<ResponsiveContainer width="100%" height={350} minWidth={1} minHeight={1}>')
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
print('ResponsiveContainer fix applied.')
