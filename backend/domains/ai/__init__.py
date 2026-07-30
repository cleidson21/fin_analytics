# backend/domains/ai/__init__.py
# Domínio AI — Gemini (Read Only).
# Responsabilidades:
#   - Fornecer análises e insights via LLM sobre dados estabilizados no banco local
#
# Restrição absoluta:
#   - NUNCA escreve no banco de dados
#   - NUNCA acessa APIs externas de forma autônoma (apenas via service público dos outros domínios)
#   - Implementado apenas na Sprint 4.7
