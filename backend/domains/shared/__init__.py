# backend/domains/shared/__init__.py
# Infraestrutura pura compartilhada entre todos os domínios.
# APENAS infraestrutura — sem regras de negócio, sem lógica de domínio.
#
# Conteúdo permitido:
#   db.py       → Engine e Session factory (SQLAlchemy)
#   config.py   → Settings (leitura de .env via pydantic-settings)
#   security.py → JWT helpers (encode/decode/verify)
#
# Proibido em shared/:
#   - Qualquer regra de negócio
#   - Qualquer referência a modelos específicos de um domínio
#   - utils.py com lógica de múltiplos domínios
