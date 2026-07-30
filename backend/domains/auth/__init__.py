# backend/domains/auth/__init__.py
# Domínio Auth — Autenticação e autorização.
# Responsabilidades:
#   - Gestão do usuário único (sistema single-user)
#   - Emissão e validação de tokens JWT
#   - Bootstrap do admin na inicialização da aplicação
#
# Limites:
#   - Não tem acesso a dados financeiros (tabelas de pierre ou myprofit)
#   - JWT helpers puros residem em shared/security.py
