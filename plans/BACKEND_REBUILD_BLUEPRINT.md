# BACKEND REBUILD BLUEPRINT (A GRANDE SÍNTESE)

Este é o documento de fundação máxima. O "Blueprint". Ele responde assertivamente aos questionamentos essenciais para a destruição do legado e construção definitiva da V3 do Backend.

---

### 1. O que o produto realmente faz?
O *FinAnalytics V2/V3* é um ecossistema holístico de Gestão Patrimonial e Financeira. Ele ingere massas de dados ruidosas (arquivos OFX, integrações B3), purifica esses dados em uma zona de quarentena (`Staging`), usa um motor híbrido de Regex/Inteligência Artificial para catalogação inteligente, resolve conflitos através de reconciliação de ±3 dias e, após aprovação humana/auditora, lança tudo em um Livro Razão Imutável (`Ledger`). A partir dessa base hiper-limpa, expõe métricas densas de *Cashflow (Pacing, Metas)* e de *Wealth (YOC, Allocation, Alpha Evolutivo)*.

### 2. Quais regras são obrigatórias?
1. **Pipeline de Inteligência Estrito:** A rota da classificação de texto é obrigatória `(Reconciliation -> Regras Locais -> IA -> Outros/Fallback)`.
2. **Singularidade do Prompt:** Nunca se pode ter duas instruções LLM/Prompts vigentes (`active=1`).
3. **Isolamento em Staging:** Nenhum dado sujo de uma nova importação `ImportRun` pode ferir o banco principal antes de passar pelo processo de Aprovação.
4. **Cascata de Exclusão (ON DELETE CASCADE):** Falha ou deleção de um `ImportRun` deve destruir sumariamente todos os metadados derivados sem restos fantasmas.

### 3. Quais cálculos são obrigatórios?
1. **Pacing de Gastos Mensal (MoM):** Gastos de `(1..Hoje) / (1..Hoje do Mês Passado) - 1`.
2. **Consumo Orçamentário (Goal Burn):** Gastos da Categoria X / Limite Mensal Definido.
3. **Yield On Cost (YOC):** Soma Total Recebida do Ativo em Dividendos / Montante Total Investido Atualmente no Ativo.
4. **Excesso de Retorno (Alpha):** Subtração entre a rentabilidade histórica do patrimônio descontando o indicador principal (Ex: IBOV/CDI).

### 4. Qual é o modelo de dados ideal?
O V2 finalizado em `schema_v2.sql`. Ele comporta perfeitamente os quatro domínios separados em tabelas tipadas: Core Finance (`transactions`), Wealth (`portfolio_evolution`, `positions`, `dividends`), Governance (`import_runs`, `audit_log`, `staging_*`) e IA (`rules`, `ai_runs`).

### 5. O que deve ser descartado?
* Toda a lógica baseada na pasta `app/api/routes` original (V1), pois não prevê a injeção dos novos serviços de Domínio e espalha o ORM.
* A prática (detectada na auditoria) dos *Services* interagirem com a *Database Session* de forma avulsa (`self.db.query`).
* Tabelas supérfluas (Ex: `event_links`, `analises`, `relatorios`).

### 6. O que deve sobreviver?
* **O Banco de Dados (Schema V2) e sua Arquitetura Relacional.**
* **Os Testes Unitários de Services** recém-criados.
* **Os Repositórios Abstratos** criados com padrão Generic (devem assumir seu posto legítimo entre o Serviço e o BD).
* **Os DTOs Pydantic** (Que devem ser a única saída permitida pela Aplicação).

### 7. Quais riscos existem para uma reconstrução completa?
O risco primordial reside no **Repository Leak**. Caso as rotas (Controllers da API V3) aceitem interagir com Models SQL diretamente ou os Services continuem retornando SQL Objects (conforme constatado no GATE-01), o frontend terá problemas de tipagem e o projeto carregará novamente a lentidão do V1. Existe a necessidade mandatória de uma refatoração pontual (vincular Services -> Repositories -> DTOs).

### 8. O banco atual suporta integralmente o domínio?
**SIM.** Com 21 tabelas muito bem indexadas e modeladas. Constraints severas como NOT NULL em `perfil` e `descricao_normalizada` (vistas quebrando testes quando desrespeitadas no V2) provam a resiliência dos dados.

### 9. O Backend V3 pode ser reconstruído apenas com os documentos produzidos?
**SIM.**

**Justificativa:** O conhecimento de negócios antes atrelado a código legado, ifs aleatórios e queries soltas está exaustivamente documentado (Cálculos, Regras, API Sobrevivente, Inventário de Tabelas). Não há mais necessidade de fazer engenharia reversa empírica a cada nova feature. Um engenheiro novo lendo o catálogo na pasta `plans/` é capaz de programar o FinAnalytics inteiramente através do contrato descrito nestes relatórios, sem sequer ler a implementação V1. O mapa do tesouro está traçado.
