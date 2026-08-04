import urllib.request
import json

try:
    req = urllib.request.Request('https://docs.pierre.finance/api-reference/openapi.json', headers={'User-Agent': 'Mozilla/5.0'})
    response = urllib.request.urlopen(req)
    openapi = json.loads(response.read().decode('utf-8'))
    
    with open('pierre_openapi.json', 'w', encoding='utf-8') as f:
        json.dump(openapi, f, indent=2, ensure_ascii=False)
        
    print(f'SUCCESS: Saved OpenAPI JSON. Keys: {list(openapi.keys())}')
    if 'paths' in openapi:
        print(f'Endpoints (Paths): {len(openapi["paths"])}')
    if 'components' in openapi and 'schemas' in openapi['components']:
        print(f'Schemas: {len(openapi["components"]["schemas"])}')
except Exception as e:
    print(f'FAILED: {e}')
