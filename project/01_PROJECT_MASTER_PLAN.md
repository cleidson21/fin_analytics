# FINANALYTICS V3 — PROJECT MASTER PLAN
> Documento permanente. **NUNCA reescrever.** Apenas receber adições controladas com data e versão.
> Última atualização: 2026-06-22

---

## 1. OBJETIVO DO SISTEMA

FinAnalytics V3 é um sistema pessoal de gestão financeira e patrimonial Single User.

**Missão:** Consolidar em uma única plataforma o controle de:
- Fluxo de caixa (transações bancárias)
- Carteira de investimentos (ações, FIIs, renda fixa, dividendos)
- Análise de patrimônio com benchmarks (IBOV, CDI, IPCA, IFIX, SP500, IDIV)
- Governança de importação (rastreabilidade, rollback, auditoria)
- Classificação por IA (regras, aprendizado, feedback)

**Usuário:** Single User. Estrutura preparada para multiusuário futuro sem refatoração de schema.

---

## 2. ESCOPO APROVADO

### Incluído
- Backend API (FastAPI + SQLite + SQLAlchemy Core)
- Frontend existente (Next.js 15 — **preservado integralmente**)
- Schema V3 congelado (migrations 001–012 + migration 013 para enrichment de classification_rules)
- Importadores: BankStatement (Pierre/CSV), MyProfit (CSV trades+dividendos), BrokerNote (PDF)
- Engines: PositionEngine (WAC), DividendEngine (YOC), WealthEngine (TWR), CashflowEngine
- AI: ClassificationService, LearningService, feedback loop
- Governança: import_runs, rollback, auditoria, reconciliação (lógica em memória)

### Excluído do escopo atual
- PostgreSQL (SQLite é definitivo para fase atual)
- Multi-user real (schema preparado, não implementado)
- Opções e contratos futuros (não modelados no PositionEngine)
- Mobile app
- Exportações PDF/Excel

---

## 3. ARQUITETURA APROVADA

```
┌─────────────────────────────────────────────────────┐
│                    FRONTEND                         │
│  Next.js 15  │  fetchFromAPI  │  NEXT_PUBLIC_API_URL │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP/REST /api/v1/
┌──────────────────────▼──────────────────────────────┐
│                    BACKEND                          │
│  FastAPI  │  Pydantic  │  SQLAlchemy Core (raw SQL) │
│                                                     │
│  domains/identity   domains/banking                 │
│  domains/credit     domains/investments             │
│  domains/governance domains/ai                      │
│  engines/           importers/                      │
│  services/market_data                               │
└──────────────────────┬──────────────────────────────┘
                       │ sqlite3
┌──────────────────────▼──────────────────────────────┐
│               DATABASE V3 (CONGELADO)               │
│  database/fin_analytics_v3.db                       │
│  Migrations 001–012 (freeze aprovado)               │
│  Migration 013 (classification_rules enrichment)    │
│  37 tabelas + índices + FK constraints              │
└─────────────────────────────────────────────────────┘
```

### Stack definitivo
| Camada | Tecnologia | Observação |
|---|---|---|
| Frontend | Next.js 15 + TypeScript | Preservado. Não alterar sem justificativa crítica. |
| HTTP Client | `lib/api.ts` + `fetchFromAPI` | Usa `NEXT_PUBLIC_API_URL` do `.env.local` |
| Backend | Python 3.11+ / FastAPI | Reconstuído do zero na pasta `backend/` |
| ORM | SQLAlchemy Core (raw SQL) | Sem ORM completo. Sem Active Record. |
| Database | SQLite 3 | Arquivo: `database/fin_analytics_v3.db` |
| Auth | JWT HS256 via `python-jose` | Single User. Seed automático. |
| Validação | Pydantic v2 | DTOs de request e response |

---

## 4. DECISÕES ARQUITETURAIS REGISTRADAS

| ID | Data | Decisão | Motivo |
|---|---|---|---|
| DA-01 | 2026-06-20 | Schema V3 congelado com 37 tabelas | Auditoria completa confirmou solidez estrutural |
| DA-02 | 2026-06-20 | Frontend preservado integralmente | É a referência visual. Trabalho mais custoso do projeto. |
| DA-03 | 2026-06-21 | Backend legado (`app/`) descartado | 0% compatibilidade com schema V3. Sem rotas HTTP ativas. |
| DA-04 | 2026-06-21 | Estratégia A: Reconstrução Total | Menor risco, zero dívida técnica, alinhamento imediato com frontend |
| DA-05 | 2026-06-21 | Reconciliação: lógica em memória | Evita novas tabelas após o freeze |
| DA-06 | 2026-06-21 | Migration 013: enriquecer `classification_rules` | Frontend exige `miss_count`, `evidence_count`, `confidence_score`, `status` |
| DA-07 | 2026-06-22 | Auth: retornar `username: user.email` | Compatibilidade com `AuthContext.tsx` sem alterar frontend |
| DA-08 | 2026-06-22 | AssetDetailPage: corrigir fetch hardcoded | Única alteração autorizada no frontend (1 linha) |

---

## 5. ROADMAP OFICIAL — 9 FASES

| Fase | Nome | Contexto Sonnet | Status |
|---|---|---|---|
| R0 | Reconciliação Documental | 1 conversa | ✅ Concluída |
| 0.9 | Governança do Projeto | 1 conversa | ✅ Aprovada |
| 1 | Fundação & Infraestrutura | 1 conversa | ✅ Aprovada |
| 2 | Identity & Autenticação | 1 conversa | ✅ Aprovada |
| 3 | Ledger Core (Banking + Dashboard) | 2 conversas | ✅ Aprovada |
| 4 | Credit & Installments | 1 conversa | ✅ Aprovada |
| 5 | Data Ingestion Platform (Ver Detalhamento) | 3 conversas | ✅ Aprovada |
| 6 | Investments & Market Data | 3 conversas | ✅ Aprovada (parcial — ver Fase 7) |
| 7 | Engines Analíticas | 3 conversas | 🔄 Em andamento |
| 8 | AI & Learning | 2 conversas | ⬜ Não iniciada |
| 9 | Validação E2E & Hardening | 1 conversa | ⬜ Não iniciada |

### Detalhamento da Fase 5 (Data Ingestion Platform)
Para isolar responsabilidades e garantir auditoria, a Fase 5 foi desmembrada em 10 subsistemas independentes:
- **5.1 Foundation**: DTOs e Repositories unificados (ImportRun, CanonicalEvent).
- **5.2 Readers**: Módulos brutos (pandas, openpyxl, pdfplumber). Sem lógica financeira.
- **5.3 OCR**: Extração em imagens (PaddleOCR, Tesseract fallback).
- **5.4 AI Parsing**: Conversão por LLM quando Regex/OCR falham.
- **5.5 Canonical Normalization**: Padronização obrigatória de todos os inputs em `Canonical Financial Event`.
- **5.6 Reconciliation**: Cruzamento e desambiguação anti-duplicidade. 
- **5.7 Governance**: Rollbacks, Warnings e Auditoria das Importações.
- **5.8 Import Engine**: Orquestração e fluxo estrito (Commit apenas no final).
- **5.9 Learning Engine**: Classificador local treinado via Teacher Forcing usando FAISS e Embeddings.
- **5.10 Open Finance**: Stubs (Adapters passivos) para integrações diretas de bancos via API (Fase Futura).

**Estimativa total:** ~18 conversas Sonnet

---

## 6. REGRAS DE OURO DO PROJETO

1. **Banco é a fonte da verdade.** Nenhuma decisão de backend pode contradizer o schema V3.
2. **Frontend é intocável.** Alterações só se houver impossibilidade técnica comprovada e documentada.
3. **Nenhuma fase avança sem gate aprovado.** Gate não aprovado = fase rejeitada = correção obrigatória.
4. **Toda decisão relevante vai ao CHANGELOG.** Nada some.
5. **Raw SQL via SQLAlchemy Core.** Nenhum ORM completo. Nenhum `Base.metadata.create_all()`.
6. **`run_id` obrigatório** em todas as tabelas append-only de importação.
7. **Tabelas analíticas são somente-leitura** para endpoints. Engines escrevem, endpoints leem.

---

## 7. CONTINUIDADE DE EXECUÇÃO

Toda nova conversa **DEVERÁ iniciar lendo OBRIGATORIAMENTE** os seguintes documentos na pasta `project/`:
1. `01_PROJECT_MASTER_PLAN.md`
2. `04_CURRENT_PHASE.md`
3. `03_PHASE_STATUS.md`
4. `09_IMPLEMENTATION_QUEUE.md`

Esses quatro documentos formam a fonte oficial para retomada. Nenhuma decisão deve depender da memória da conversa anterior.

---

## 8. GOVERNANÇA DE FASES E OBRIGAÇÃO DE ATUALIZAÇÃO

Ao final de **TODA fase aprovada**, é **OBRIGATÓRIO** atualizar os seguintes documentos de controle:
- **`01_PROJECT_MASTER_PLAN.md`**: Registrar a fase concluída, entregáveis e decisões tomadas.
- **`02_PROJECT_CHANGELOG.md`**: Registrar mudanças executadas.
- **`03_PHASE_STATUS.md`**: Atualizar status da fase (de `Em andamento` para `Aprovada`).
- **`04_CURRENT_PHASE.md`**: Mover para a próxima fase.
- **`05_TEST_PLAN.md`**: Registrar resultado dos testes.
- **`06_AUDIT_LOG.md`**: Adicionar auditoria realizada.
- **`09_IMPLEMENTATION_QUEUE.md`**: Atualizar a fila com as próximas tarefas, atualizar status da tarefa atual.

---

## 9. CRITÉRIO UNIVERSAL DE APROVAÇÃO (GATE UNIVERSAL)

Uma fase **SOMENTE** pode ser aprovada quando:
1. Entregáveis concluídos
2. Testes concluídos
3. Auditoria concluída
4. Documentação atualizada (arquivos acima)
5. **Evidências anexadas**

### Evidências Obrigatórias
Cada fase deve apresentar, de forma explícita:
- Endpoints testados localmente (ou via scripts unitários)
- JSON de resposta do payload
- Logs relevantes do terminal
- Relatório de testes
- Problemas encontrados e corrigidos
- **[A partir da Fase 5] 4 Níveis de Auditoria:**
  1. Testes unitários (`pytest`)
  2. Pacote funcional End-to-End (`tests/results/.../`) contendo JSONs e Markdown Reports gerados a partir de `samples/`
  3. Golden Test Visual (geração de `canonical_events.csv` interpretável)
  4. Fluxograma Rastreável (`pipeline.txt` demonstrando aprovação/bloqueio no Governance)

**Sem evidências apresentadas ao usuário, o Gate NÃO PODE ser aprovado e a fase permanece em Auditoria.**

---

## 10. HIERARQUIA DE GOVERNANÇA DOCUMENTAL

> **Regra permanente.** Estabelecida na Fase R0 (2026-07-14) para evitar desvios de nomenclatura e roadmaps paralelos.

Toda alteração documental deverá obedecer OBRIGATORIAMENTE a seguinte ordem de atualização:

```
01_PROJECT_MASTER_PLAN.md   ← Atualizar primeiro (somente Status)
        ↓
03_PHASE_STATUS.md
        ↓
04_CURRENT_PHASE.md
        ↓
09_IMPLEMENTATION_QUEUE.md
        ↓
02_PROJECT_CHANGELOG.md
        ↓
06_AUDIT_LOG.md
```

**Nenhum documento poderá ser alterado antes que o imediatamente superior na hierarquia tenha sido atualizado.**

### Proibições absolutas
- Nunca criar novas Fases fora deste Master Plan sem aprovação explícita do usuário
- Nunca criar novo Roadmap paralelo
- Nunca alterar arquitetura sem aprovação explícita
- Nunca nomear Gates como se fossem Fases independentes

---

## 11. REGRAS PARA IA E AGENTES

> **Leitura obrigatória para qualquer agente ou sessão nova.**

Todo agente de IA **DEVE**, obrigatoriamente, **antes de executar qualquer alteração**:

1. Ler `01_PROJECT_MASTER_PLAN.md` (este arquivo)
2. Ler `03_PHASE_STATUS.md`
3. Ler `04_CURRENT_PHASE.md`
4. Ler `09_IMPLEMENTATION_QUEUE.md`
5. Ler `06_AUDIT_LOG.md`

Caso encontre **qualquer divergência** entre esses documentos:
- **Interromper imediatamente** a implementação
- **Abrir uma Auditoria de Governança** antes de prosseguir
- **Nunca criar Fases, Gates ou Roadmaps novos** sem aprovação explícita
- **Consultar `34_ARCHITECTURE_RECONCILIATION.md`** para entender a história dos desvios anteriores e como foram corrigidos

**Violação desta regra é considerada desvio arquitetural de Nível Crítico.**
