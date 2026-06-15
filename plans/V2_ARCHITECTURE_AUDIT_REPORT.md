# V2 ARCHITECTURE AUDIT REPORT (GATE-01)

Este documento apresenta a auditoria técnica completa da arquitetura Backend V2, validando a conformidade entre as camadas de Banco de Dados, Modelos ORM, Repositórios, Serviços e DTOs, antecedendo o início da reconstrução da API (BE-03).

---

## 1. Divergências Database ↔ ORM
**Status: ✅ Em Conformidade**
A sincronia entre `database/schema_v2.sql` e as classes em `app/models/*.py` está excelente.
* Todas as PKs, FKs, constraints de integridade (ON DELETE CASCADE, UNIQUE) e tipos de colunas foram mapeados com precisão.
* *Nota Técnica*: A coluna `metadata` na tabela `raw_events` do DB foi corretamente mapeada no ORM como `metadata_json = Column("metadata", ...)` para contornar palavras reservadas do SQLAlchemy, evidenciando uma implementação robusta.

---

## 2. Divergências ORM ↔ Repository
**Status: ✅ Em Conformidade**
* Todas as 21 tabelas/models do sistema possuem um Repository específico (ex: `TransactionRepository`, `PositionRepository`, `RuleRepository`).
* Não existem "repositories órfãos".
* Todos os repositórios herdam corretamente de `BaseRepository[ModelType]`.

---

## 3. Divergências Repository ↔ Service
**Status: ❌ CRÍTICO (Divergência Encontrada)**
* A regra de arquitetura exige que "todos os services usam repositories" e "nenhum service abre Session diretamente para queries ORM".
* **Realidade**: Todos os Services construídos nas Sprints BE-02 (`CashflowService`, `PositionService`, `ImportService`, `RuleEngineService`, etc.) **ignoram** os Repositories criados. Eles injetam `db: Session` nos contrutores e fazem as consultas invocando nativamente `self.db.query(Model)`.
* *Risco*: Os Repositories atuais são meras interfaces zumbis no sistema, não operando o funil do CRUD planejado.

---

## 4. Divergências Service ↔ DTO
**Status: ❌ CRÍTICO (Divergência Encontrada)**
* A regra exige que as respostas não retornem o ORM cru.
* **Realidade**: Praticamente todos os serviços retornam Dicionários Python puros (ex: `{ "matched": True }`) ou objetos diretos do SQLAlchemy (ex: instâncias de `ImportRun` ou `PromptVersion`).
* Nenhuma amarração firme com os schemas em `app/schemas/*.py` ocorre internamente aos Services (que é a prática ideal para Domain-Driven Validation).

---

## 5. Matriz de Endpoints (API CONTRACT FREEZE)

| Rota Original V1 (Endpoint) | Domínio | Status / Ação V2 | Observação |
| :--- | :--- | :--- | :--- |
| `GET /dashboard/pacing` | Dashboard | **Substituir** | Adaptar para Pace-V2 |
| `GET /dashboard/summary` | Dashboard | **Reutilizar** | Adaptar injeção do Cashflow V2 |
| `GET /transactions` | Core | **Reutilizar** | Roteamento principal do app |
| `PATCH /transactions/{id}/reclassify`| Core | **Substituir** | Adotar Workflow de Governance |
| `GET /investments/dividends/*` | Wealth | **Consolidar** | Redirecionar para `DividendService` |
| `GET /investments/evolution/*` | Wealth | **Consolidar** | Redirecionar para `PortfolioEvolution` |
| `GET /investments/positions` | Wealth | **Reutilizar** | Roteamento nativo de Tickers |
| `POST /governance/import-pierre` | Governance | **Remover** | Será `ImportService` Genérico V2 |
| `POST /governance/import-myprofit` | Governance | **Remover** | Será `ImportService` Genérico V2 |
| `GET /governance/imports` | Governance | **Substituir** | Ajustar para as novas Staging Tables |
| `POST /governance/imports/{id}/confirm` | Governance | **Substituir** | Acionar novo `ApprovalService` |
| `GET /governance/audit-logs` | Governance | **Reutilizar** | Nova lógica de Log em DB |
| `GET /learning/rules` | AI Layer | **Reutilizar** | Adaptar pro `RuleEngineService` |
| `POST /prompts` | AI Layer | **Substituir** | Usar novo pipeline PromptVersion |

---

## 6. Dependências Circulares
**Status: ✅ Saudável**
* **Inexistentes**: O V2 obedeceu a estratégia "Vertical Slices".
* Os repositories não chamam serviços.
* Apenas foi mapeado o `ClassificationEngineService` chamando o `RuleEngineService`, o que é **100% legal** por estarem na mesma camada/Bounded Context (AI Layer) desenhada no Pipeline de Classificação.

---

## 7. Riscos Críticos Identificados
1. **Repository Leak:** Os *Controllers/Routers* da BE-03 não devem lidar com Modelos ORM, mas como os *Services* não estão injetando schemas via DTO e não usam Repositories, o Frontend irá quebrar ou a refatoração do FastApi será demasiadamente caótica.
2. **Coupling**: Acoplamento das queries complexas nos Services quebra o padrão de Injeção de Dependências puro estipulado no REBUILD.

---

## 8. Conclusão Final

### GO / NO-GO para BE-03 (API Reconstruction)
**Decisão: 🔴 NO-GO (Parcial)**

**Fundamento:** A fundação e regras de negócios funcionam esplendidamente, mas o padrão de implementação da Arquitetura Limpa nos arquivos foi violado (Services ignorando Repositories e não respondendo via DTOs). 

**Recomendação Exclusiva:** Solicito a decisão do **Arquiteto Chefe (USER)**:
1. **Opção A:** Realizar uma *Sprint BE-02.5 (Refactoring)* onde refatoro rapidamente os Services para consumirem os Repositories criados e cuspir DTOs.
2. **Opção B:** Emitir o "Override / GO" para BE-03, estipulando que o ajuste dos Services/Repositories deverá ser consertado concomitantemente à escrita dos novos endpoints.
