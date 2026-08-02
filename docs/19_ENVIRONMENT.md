> [!IMPORTANT]
> A pasta docs/ é a única fonte oficial de documentação do projeto. É proibido criar documentação fora dela. Toda nova implementação deve ler os documentos existentes em docs/, atualizá-los quando necessário e registrar decisões arquiteturais por meio de ADRs antes de prosseguir.

# Configuração de Ambiente (.env)

Este documento centraliza todas as variáveis de ambiente, sua finalidade, quem as consome e como são carregadas.

## Variáveis do Sistema

### PIERRE_API_KEY
- **Uso:** Autenticação MCP e API REST da Pierre.
- **Quem consome:** Python (via ackend/core/config.py), VS Code (settings.json), Node/MCP (via script PowerShell start_mcp.ps1).
- **Obrigatoriedade:** Obrigatório para integrações Pierre.
- **Formato:** String (ex: sk-...).
- **Como é carregada:** Pelo Pydantic no backend. Pelo script PowerShell que exporta para $env:PIERRE_API_KEY antes de iniciar o Node.

### GEMINI_API_KEY / OPENAI_API_KEY
- **Uso:** Classificação via IA.
- **Quem consome:** Python.
- **Obrigatoriedade:** Opcional.
- **Formato:** String.

### MYPROFIT_USERNAME / MYPROFIT_PASSWORD
- **Uso:** Credenciais do portal.
- **Quem consome:** Python.
- **Obrigatoriedade:** Obrigatório para ingestão MyProfit.

### DATABASE_URL
- **Uso:** Conexão do SQLAlchemy e Alembic.
- **Quem consome:** Python.
- **Obrigatoriedade:** Obrigatório.
- **Formato:** URL (ex: sqlite:///./database/fin_analytics.db).

### JWT_SECRET / JWT_EXPIRE_MINUTES
- **Uso:** Autenticação local FIN Analytics.
- **Quem consome:** Python.
- **Obrigatoriedade:** Obrigatório.

### ENVIRONMENT
- **Uso:** Controlar o ambiente (development, production).
- **Quem consome:** Python.
- **Obrigatoriedade:** Obrigatório.

## Resolução de Problemas
**O MCP não consegue ler minha chave!**
O arquivo .env **não** exporta as variáveis automaticamente para o sistema operacional Windows. Para iniciar o MCP, você deve obrigatoriamente utilizar o inicializador oficial: .\scripts\start_mcp.ps1.
