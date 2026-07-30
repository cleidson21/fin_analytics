"""
schemas.py — Domínio Pierre

DTOs Pydantic para:
  - Payload bruto recebido da API Pierre (input/validação)
  - Resposta serializada para o Frontend (output/contrato público)

Princípios:
  - O schema de input espelha exatamente o contrato da API Pierre
  - Nenhum campo é inventado ou deduzido
  - Campos desconhecidos recebidos da Pierre vão para extra_json (campo catch-all)
  - Schemas são os contratos públicos de comunicação inter-domínios
"""

# TODO Sprint 4.4.1 — implementar Pydantic schemas
