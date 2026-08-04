import json

openapi = json.load(open('pierre_openapi.json', encoding='utf-8'))
paths = openapi['paths']
servers = openapi.get('servers', [])
tags = openapi.get('tags', [])

print("=== SERVERS ===")
for s in servers:
    print(s.get('url'))

print("\n=== TAGS ===")
for t in tags:
    print(t.get('name'), '-', t.get('description', ''))

print("\n=== PATHS ===")
for path, methods in paths.items():
    for method, details in methods.items():
        params = details.get('parameters', [])
        print(f"{method.upper()} {path}")
        print(f"  summary: {details.get('summary', '')}")
        print(f"  tags: {details.get('tags', [])}")
        for p in params:
            pname = p.get('name')
            pin = p.get('in')
            preq = p.get('required', False)
            psch = p.get('schema', {})
            ptype = psch.get('type', '?')
            print(f"  param [{pin}] {pname}: type={ptype} required={preq}")
        rb = details.get('requestBody', {})
        if rb:
            content = rb.get('content', {}).get('application/json', {}).get('schema', {})
            ref = content.get('$ref', content.get('type', ''))
            print(f"  body: {ref}")
        responses = details.get('responses', {})
        for code, resp in responses.items():
            print(f"  response {code}: {resp.get('description', '')}")
        print()
