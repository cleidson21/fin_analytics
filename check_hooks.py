import os, sys, re
sys.stdout.reconfigure(encoding='utf-8')

hooks = [
    'frontend/src/hooks/useGrowthData.ts',
    'frontend/src/hooks/useDividendsData.ts',
    'frontend/src/hooks/useAlphaData.ts',
    'frontend/src/hooks/useAllocationData.ts',
    'frontend/src/hooks/usePerformanceData.ts',
    'frontend/src/hooks/usePositionsData.ts',
]
for h in hooks:
    if os.path.exists(h):
        with open(h, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            endpoints = re.findall(r'["\']/([\w/._\-{}]+)["\']', content)
            print(f'{os.path.basename(h)}: {endpoints[:5]}')

print()
# Check backend for governance domain
for root, dirs, files in os.walk('backend/domains'):
    dirs[:] = [d for d in dirs if d not in ['__pycache__']]
    for f in files:
        if 'governance' in f or 'dividend' in f or 'dividend' in root:
            print(f'File: {os.path.join(root, f)}')

# Check main.py
with open('backend/main.py', 'r', encoding='utf-8') as f:
    print('backend/main.py:')
    print(f.read())
