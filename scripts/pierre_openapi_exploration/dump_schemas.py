import json

openapi = json.load(open('pierre_openapi.json', encoding='utf-8'))
schemas = openapi['components']['schemas']

for name, schema in schemas.items():
    props = schema.get('properties', {})
    if props:
        print(f'--- {name} ---')
        req_fields = schema.get('required', [])
        for k, v in props.items():
            t = v.get('type', v.get('$ref', '[ref]'))
            nullable = v.get('nullable', False)
            is_req = k in req_fields
            enum_vals = v.get('enum', None)
            desc = v.get('description', '')
            out = f'  {k}: type={t} required={is_req} nullable={nullable}'
            if enum_vals:
                out += f' enum={enum_vals}'
            if desc:
                out += f' // {desc}'
            print(out)
