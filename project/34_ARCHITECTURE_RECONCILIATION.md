# 34 — ARCHITECTURE RECONCILIATION
## Registro Permanente de Desvios Documentais e Correções
**Criado em:** 2026-07-14 | **Fase:** R0 — Reconciliação Documental

> Este documento é **append-only** e **permanente**.
> Nunca modifique entradas existentes. Adicione novas seções para desvios futuros.
> Consulte este arquivo antes de iniciar qualquer nova sessão de implementação.

---

## 1. DESVIO DR-001 — Nomenclatura "Gate 10.x" como Roadmap Paralelo

### 1.1 Por que surgiu o Gate 10.x

Durante as Sprints 6 e 7 (2026-07-12 a 2026-07-13), as sessões de implementação foram executadas de forma autônoma por Agentes de IA sem leitura prévia obrigatória do Master Plan e dos documentos de controle.

Cada sessão seguia a lógica de "próximo Gate" sem verificar se a nomenclatura dos gates correspondia às Fases oficiais. O padrão emergiu de forma orgânica:
- Sprint 6 usou Gates 9.x (correto — Fase 6/7 são sprints de Investments)
- Sprint 7 criou Gates 10.x como "próxima sequência" sem verificar o Master Plan

Como resultado, os Gates 10.1 a 10.13 foram registrados em todos os documentos de controle como se existisse uma "Fase 10" no projeto, quando o Master Plan define apenas 9 Fases (0.9 → 9).

### 1.2 Como a divergência ocorreu

O problema foi de **ausência de salvaguarda**, não de má intenção:

1. **Falta de leitura obrigatória**: Nenhuma regra formal exigia que o Agente lesse `03_PHASE_STATUS.md` e `04_CURRENT_PHASE.md` antes de iniciar.
2. **Falta de regra contra novos roadmaps**: O Master Plan não explicitava que criar novas Fases requereria aprovação explícita.
3. **Documentos de controle desatualizados**: `04_CURRENT_PHASE.md` apontava para "Fase 3" (desatualizado), não fornecendo referência confiável para os Agentes.
4. **Ausência de hierarquia documental formalizada**: Sem regra clara de qual documento tem autoridade sobre qual, cada sessão interpretava os documentos de forma independente.

### 1.3 Quais Gates foram afetados e sua reclassificação

| Gate Original | Nomenclatura Incorreta | Reclassificação Correta | Fase do Master Plan |
|---|---|---|---|
| Gate 10.1 | "Sprint 7, Fase 10.1" | Fase 7, Sprint 7 — Pipeline Real de Importação | Fase 7 |
| Gate 10.2 | "Sprint 7, Fase 10.2" | Fase 7, Sprint 7 — Ledger de Importações | Fase 7 |
| Gate 10.3 | "Sprint 7, Fase 10.3" | Fase 7, Sprint 7 — Séries Temporais | Fase 7 |
| Gate 10.4 | "Sprint 7, Fase 10.4" | Fase 7, Sprint 7 — Market Data Engine | Fase 6/7 |
| Gate 10.5 | "Sprint 7, Fase 10.5" | Fase 7, Sprint 7 — Validação E2E Engines | Fase 7 |
| Gate 10.6 | "Sprint 7, Fase 10.6" | Fase 7, Sprint 7 — History Engine Incremental | Fase 7 |
| Gate 10.7 | "Sprint 7, Fase 10.7" | Fase 7, Sprint 7 — Historical Asset Pricing | Fase 7 |
| Gate 10.8 | "Sprint 7, Fase 10.8" | Fase 7, Sprint 7 — Financial Analytics Engine | Fase 7 |
| Gate 10.9 | "Sprint 7, Fase 10.9" | Fase 7, Sprint 7 — Application Service Layer/DI | Fase 7 |
| Gate 10.10 | "Sprint 7, Fase 10.10" | Fase 7, Sprint 7 — Portfolio Dashboard API | Fase 7 |
| Gate 10.11 | "Sprint 7, Fase 10.11" | Fase 7, Sprint 7 — API Contract & Stabilization | Fase 9 (antecipado) |
| Gate 10.12 | "Sprint 7, Fase 10.12" | Fase 7, Sprint 7 — Frontend Readiness | Fase 9 (antecipado) |
| Gate 10.13 | "Sprint 7, Fase 10.13" | Fase 7, Sprint 7 — Auditoria Arquitetural | Fase 7 |

**Importante:** Os Gates 10.x são implementações **válidas e aprovadas**. Apenas a nomenclatura foi corrigida. O conteúdo permanece intacto no código e na documentação histórica.

### 1.4 Como foi corrigida

A Fase R0 (Reconciliação Documental) executou as seguintes correções em ordem hierárquica:

1. **`01_PROJECT_MASTER_PLAN.md`**: Status das Fases atualizado. Seções 10 (Hierarquia de Governança) e 11 (Regras para IA) adicionadas como salvaguarda permanente.
2. **`03_PHASE_STATUS.md`**: Status corretos restaurados. Gates 10.x reclassificados dentro da Fase 7.
3. **`04_CURRENT_PHASE.md`**: Reescrito apontando para Fase 7. Estado pós-Gate 10.13 documentado.
4. **`09_IMPLEMENTATION_QUEUE.md`**: Tarefa atual correta (TSK-7.R1). "Fases R1-R4" convertidas em tarefas da Fase 7.
5. **`02_PROJECT_CHANGELOG.md`**: Gates 10.x regularizados em bloco `### [2026-07-13] FASE 7`.
6. **`06_AUDIT_LOG.md`**: Entrada R0 adicionada.
7. **`31`, `32`, `33`**: Edição 3 com achados da Sprint 7.
8. **`34_ARCHITECTURE_RECONCILIATION.md`**: Este documento criado.

### 1.5 Nomenclatura oficial confirmada

A partir de 2026-07-14, a nomenclatura oficial é:

```
Fase 7 — Engines Analíticas & Pipelines
    Sprint 7
        Gate 10.1   ← identificador interno da Sprint 7
        Gate 10.2   ← identificador interno da Sprint 7
        ...
        Gate 10.13  ← identificador interno da Sprint 7
```

Os números "10.x" são **identificadores internos de gates da Sprint 7** e não representam uma Fase separada. Nas referências históricas eles permanecem como estavam, com uma nota de reconciliação.

---

## 2. DESVIO DR-002 — "Fases R1-R4" como Pseudo-Fases Oficiais

### 2.1 Por que surgiu

O Gate 10.13 propôs um "Plano de Reconciliação" com "Fases R1 a R4" que foram parcialmente incorporadas ao `09_IMPLEMENTATION_QUEUE.md` como estrutura de fases.

### 2.2 Como foi corrigida

As "Fases R1-R4" foram reclassificadas como **Tarefas da Fase 7** com IDs TSK-7.R1, TSK-7.R2, TSK-7.R3 e TSK-7.R4.

### 2.3 Nomenclatura oficial confirmada

```
Fase 7 — Engines Analíticas & Pipelines
    ...
    TSK-7.R1 — Reconectar Repositories ao V3          [PENDENTE]
    TSK-7.R2 — Otimizar leitura do Dashboard           [PENDENTE]
    TSK-7.R3 — Construir endpoints faltantes           [PENDENTE]
    TSK-7.R4 — Certificação Frontend E2E               [PENDENTE]
    TSK-7.INT — Integrações Externas                   [PENDENTE]
```

---

## 3. SALVAGUARDAS PERMANENTES ESTABELECIDAS

### 3.1 Hierarquia de Autoridade Documental

```
01_PROJECT_MASTER_PLAN.md   ← AUTORIDADE MÁXIMA (imutável exceto Status)
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

**Nenhum documento pode ser alterado antes que o imediatamente superior tenha sido atualizado.**

### 3.2 Regras para IA e Agentes (resumo)

Ver `01_PROJECT_MASTER_PLAN.md` Seção 11 para a versão completa.

Resumo operacional:

1. **LEITURA OBRIGATÓRIA antes de qualquer ação:** `01_PROJECT_MASTER_PLAN.md`, `03_PHASE_STATUS.md`, `04_CURRENT_PHASE.md`, `09_IMPLEMENTATION_QUEUE.md`, `06_AUDIT_LOG.md`
2. **Se encontrar divergência:** Interromper imediatamente. Abrir Auditoria de Governança.
3. **Nunca criar novas Fases** sem aprovação explícita do usuário.
4. **Nunca criar Gates como se fossem Fases** — Gates são subtarefas de Sprints dentro de Fases.
5. **Nunca criar novo Roadmap** — o Master Plan é o único roadmap oficial.
6. **Consultar este arquivo** para entender o histórico dos desvios anteriores.

### 3.3 Proibições absolutas

- ❌ Criar "Fase 10", "Fase 11" ou qualquer fase não prevista no Master Plan sem aprovação
- ❌ Incorporar resultados de gates em documentos de controle como "fases"
- ❌ Modificar o CHANGELOG sem seguir o formato `### [DATA] FASE X — Nome`
- ❌ Alterar `01_PROJECT_MASTER_PLAN.md` exceto o campo Status das Fases

---

## 4. COMO REGISTRAR DESVIOS FUTUROS

Caso um novo desvio seja identificado, adicionar uma nova seção neste arquivo:

```markdown
## [N+1]. DESVIO DR-00X — [Nome do Desvio]

### X.1 Por que surgiu
[descrição]

### X.2 Como a divergência ocorreu
[descrição]

### X.3 Como foi corrigida
[descrição]

### X.4 Nomenclatura oficial confirmada
[descrição]
```

E registrar no `06_AUDIT_LOG.md` uma entrada correspondente.

---

**Responsável pela criação:** Agente AI (Google DeepMind)
**Aprovado por:** Usuário (decisões de reconciliação aprovadas em 2026-07-14)
