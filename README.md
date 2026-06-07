# Fin Analytics V2

Bem-vindo ao **Fin Analytics V2**, um sistema corporativo completo para governança, controle e curadoria de dados financeiros pessoais e investimentos (Wealth).

## Arquitetura do Sistema

O projeto é dividido em módulos claros para garantir separação de responsabilidades, estabilidade de APIs e forte governança de dados:

- **Frontend (`/frontend/`)**: Interface rica criada com Next.js (App Router), React, TailwindCSS e lucide-react. Oferece visualização unificada (Dashboard, Wealth, e Área Administrativa).
- **Backend (`/app/`)**: Motor de APIs desenvolvido em Python usando o framework FastAPI. Responsável por todos os cálculos patrimoniais, curadoria de importação, pipelines de IA e regras de negócio.
- **Banco de Dados (`/database/`)**: Armazena os dados através de banco SQLite nativo (com tabelas para transações, posições, dividendos, usuários e *audit_log*).

## Como Iniciar

O sistema deve rodar simultaneamente os servidores Frontend e Backend.

### 1. Backend (FastAPI)
Abra um terminal na raiz do projeto, ative o ambiente virtual e inicie o Uvicorn:
```powershell
.venv\Scripts\activate
uvicorn app.api.main:app --reload
```

### 2. Frontend (Next.js)
Abra um segundo terminal, navegue até a pasta frontend e inicie o servidor de desenvolvimento:
```powershell
cd frontend
npm run dev
```
Acesse a plataforma em `http://localhost:3000`.

## Estrutura do Repositório (Raiz Limpa)

A raiz do projeto foi arquitetada para conter estritamente o necessário:

- `app/`: Código fonte do backend em Python.
- `frontend/`: Código fonte do frontend em TypeScript/React.
- `database/`: Banco de dados atualizado da aplicação.
- `archive/`: Armazena todos os códigos legados (como scrapers antigos), dumps de bancos inativos e arquivos de importação fundadores da versão anterior (`bootstrap-data`).
- `ROADMAP.md`: Controle de escopo de cada Fase.
- `.gitignore` & `requirements.txt`: Infraestrutura de dependências.

---
Desenvolvido como plataforma de *Wealth Management* & *Data Governance*.
