<div align="center">
  <h1>📈 Fin Analytics V2</h1>
  <p><strong>Plataforma Corporativa de Wealth Management & Inteligência Financeira</strong></p>
  
  [![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
  [![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
  [![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
  [![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org/index.html)
  [![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
</div>

<br />

Bem-vindo ao **Fin Analytics V2**, um ecossistema financeiro projetado para ir além do simples registro de gastos. Ele consolida **Controle Financeiro de Alta Fidelidade**, **Wealth Management Avançado (Investimentos)**, **Governança de Dados Estrita** e um robusto **Pipeline Pró-IA**.

## ✨ Principais Funcionalidades

- **🏛️ Governança de Dados (Data Governance):** Curadoria visual de dados, saneamento, ferramentas de *merge* de categorias, e validação rigorosa pré-importação. Ambiente preparado para garantir 100% de confiabilidade matemática (Audit-and-Fix).
- **💼 Wealth Engine:** Dashboard avançado para acompanhamento de carteira de investimentos. Controle de rentabilidade, *Asset Allocation*, evolução patrimonial e análise de Dividendos/Proventos (Yield on Cost, Históricos).
- **🤖 Preparação para IA (Governança Inteligente):** Estrutura desenhada para integração nativa com LLMs (Gemini). Sistema de auditoria rigoroso para criar *few-shots* de aprendizado contínuo através da categorização do próprio usuário.
- **🛡️ Auditoria Inquebrável:** Logs de auditoria automáticos (`audit_log`) registram toda e qualquer mutação de dados da aplicação, permitindo rastreabilidade contínua de operações sensíveis.

---

## 🏗️ Arquitetura do Sistema

A solução adota uma arquitetura modular moderna e escalável, dividindo claramente as responsabilidades:

* **Frontend (`/frontend/`)**
  * Desenvolvido em **Next.js 14+ (App Router)** com **React** e tipagem estrita em **TypeScript**.
  * Interface premium estilizada via **TailwindCSS**, com iconografia do **Lucide React**.
  * Arquitetura de componentes modular focada em reusabilidade e *performance* livre de *re-renders* excessivos.

* **Backend (`/app/`)**
  * Motor financeiro em **Python** utilizando **FastAPI**.
  * Responsável pelo processamento assíncrono pesado, *ETLs*, validação de regras de negócio, e conexão segura com a persistência de dados.

* **Banco de Dados (`/database/`)**
  * **SQLite nativo** perfeitamente estruturado (`fin_analytics.db`). 
  * Esquema altamente normalizado contando com tabelas de *staging* para importação segura e trilha de auditoria completa.

---

## 🚀 Como Iniciar (Getting Started)

O sistema exige a execução simultânea dos serviços de Backend e Frontend.

### Pré-requisitos
- Python 3.10+
- Node.js 18+ & npm

### 1. Inicializando o Backend (API)
Abra um terminal na raiz do projeto, ative o ambiente virtual e inicie o servidor:

```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

# Iniciar Uvicorn
uvicorn app.api.main:app --reload
```
A documentação interativa da API ficará disponível em: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Inicializando o Frontend (Next.js)
Abra um segundo terminal, instale as dependências e inicie o cliente de desenvolvimento:

```bash
cd frontend
npm install
npm run dev
```
Acesse a aplicação completa em: [http://localhost:3000](http://localhost:3000)

---

## 📂 Estrutura do Repositório (Raiz Limpa)

A raiz do projeto foi refatorada sob a premissa de *Clean Architecture* e organização minimalista:

```text
fin_analytics_v2/
├── app/                  # Código-fonte do Backend (Python/FastAPI)
├── frontend/             # Código-fonte do Frontend (Next.js/React)
├── database/             # Arquivos do DB (Schema, Migrations e o próprio SQLite)
├── archive/              # Dumps inativos, scripts de ETL legados e bootstrap-data
├── ROADMAP.md            # Planejamento estratégico e controle rigoroso de fases
└── requirements.txt      # Dependências do motor Python
```

---

<div align="center">
  <sub>Construído com excelência estrutural e tolerância zero a bugs matemáticos.</sub>
</div>
