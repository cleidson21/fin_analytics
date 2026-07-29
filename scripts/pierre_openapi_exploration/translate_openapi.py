import json
import os

with open('pierre_openapi.json', 'r', encoding='utf-8') as f:
    openapi = json.load(f)

docs_dir = 'docs'
os.makedirs(docs_dir, exist_ok=True)

# 1. 20_REST_ENDPOINTS.md
with open(os.path.join(docs_dir, '20_REST_ENDPOINTS.md'), 'w', encoding='utf-8') as f:
    f.write("> [!IMPORTANT]\n> A pasta `docs/` é a única fonte oficial de documentação do projeto.\n\n")
    f.write("# Endpoints REST (Pierre Finance) [EXTRAÍDOS DO OPENAPI]\n\n")
    
    paths = openapi.get('paths', {})
    for path, methods in paths.items():
        for method, details in methods.items():
            f.write(f"## {method.upper()} {path}\n")
            f.write(f"- **Summary:** {details.get('summary', '[PENDENTE]')}\n")
            f.write(f"- **Description:** {details.get('description', '[PENDENTE]')}\n")
            f.write(f"- **Operation ID:** {details.get('operationId', '[PENDENTE]')}\n")
            
            params = details.get('parameters', [])
            if params:
                f.write("- **Parameters:**\n")
                for p in params:
                    required = "Obrigatório" if p.get('required') else "Opcional"
                    f.write(f"  - `{p.get('name')}` ({p.get('in')}): {required} - {p.get('description', '')}\n")
            else:
                f.write("- **Parameters:** Nenhum\n")
                
            req_body = details.get('requestBody', {})
            if req_body:
                f.write("- **Body:** [CONFIRMADO] Requer payload.\n")
            
            responses = details.get('responses', {})
            f.write("- **Responses:**\n")
            for status, resp in responses.items():
                f.write(f"  - `{status}`: {resp.get('description', '')}\n")
            
            f.write("\n")

# 2. 21_PROVIDER_MODELS.md & 24_JSON_SCHEMAS.md
with open(os.path.join(docs_dir, '21_PROVIDER_MODELS.md'), 'w', encoding='utf-8') as f:
    f.write("> [!IMPORTANT]\n> A pasta `docs/` é a única fonte oficial de documentação do projeto.\n\n")
    f.write("# Modelos Canônicos Extraídos (Pierre Finance)\n\n")
    
    schemas = openapi.get('components', {}).get('schemas', {})
    for name, schema in schemas.items():
        f.write(f"## {name} [CONFIRMADO]\n")
        f.write(f"- **Type:** {schema.get('type', 'object')}\n")
        f.write(f"- **Description:** {schema.get('description', '')}\n\n")
        f.write("### Campos\n")
        
        properties = schema.get('properties', {})
        required_fields = schema.get('required', [])
        
        if not properties:
            f.write("Nenhum campo documentado.\n\n")
            continue
            
        for prop_name, prop_details in properties.items():
            req_str = "Obrigatório" if prop_name in required_fields else "Opcional"
            ptype = prop_details.get('type', '[REF]')
            
            # handle arrays or refs
            if 'items' in prop_details:
                ptype = f"array of {prop_details['items'].get('type', 'ref')}"
                
            f.write(f"- `{prop_name}` ({ptype}): {req_str}. {prop_details.get('description', '')}\n")
        f.write("\n")

# Copy the schemas identical to models per prompt instruction
with open(os.path.join(docs_dir, '24_JSON_SCHEMAS.md'), 'w', encoding='utf-8') as f:
    with open(os.path.join(docs_dir, '21_PROVIDER_MODELS.md'), 'r', encoding='utf-8') as src:
        f.write(src.read().replace('Modelos Canônicos Extraídos', 'JSON Schemas'))

print("Gerados documentos baseados no OpenAPI.")
