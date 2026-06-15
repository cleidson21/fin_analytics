import re
import os

results = set()
for root, dirs, files in os.walk('app'):
    for file in files:
        if file.endswith('.py'):
            content = open(os.path.join(root, file), 'r', encoding='utf-8').read()
            matches = re.findall(r'[\"\']([A-Z_]+)[\"\']', content)
            results.update(matches)

schema = open('database/schema.sql', 'r', encoding='utf-8').read()
schema_statuses = set(re.findall(r'DEFAULT [\'\"]([A-Z_]+)[\'\"]', schema))

print('Hardcoded Strings:', [s for s in results if s in ['PENDING', 'PROCESSING', 'PENDING_CONFIRMATION', 'CONFIRMED', 'FAILED', 'ROLLED_BACK', 'CANCELLED', 'UPLOADED', 'GENERATED', 'OBSERVING', 'PENDING_APPROVAL', 'APPROVED', 'RETIRED', 'CREATED', 'ANALYZED', 'INCORPORATED', 'REJECTED', 'RUNNING', 'SUCCESS']])
print('Schema Default States:', schema_statuses)
