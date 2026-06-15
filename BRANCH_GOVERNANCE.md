# BRANCH GOVERNANCE - FASE 10.1

Este documento estabelece as regras arquiteturais definitivas para o fluxo de reengenharia (V2) do Fin Analytics.

A branch `main` passa a atuar como um repositório imutável de consulta (System Freeze). Nenhuma feature será desenvolvida nela. Todo o ciclo de vida do novo produto ocorrerá de forma segmentada e orquestrada pelas novas ramificações.

---

## 1. ESTRUTURA E OBJETIVOS DAS BRANCHES

* **`main` (Congelada)**
  * **Objetivo:** Ponto de restauração absoluto e histórico documentado. Contém o pacote `SYSTEM_REBUILD_PACKAGE.md` e o código da fase de transição (V1.5).
  * **Responsabilidade:** Servir de espelho consultivo. Só recebe merges em caso de patches de segurança emergenciais em ferramentas documentais.

* **`legacy-v1`**
  * **Objetivo:** Arquivamento do MVP inicial. Útil para consultar lógicas superadas que foram depreciadas do modelo V2 (como a tabela `etl_runs_legacy`).
  * **Responsabilidade:** Apenas leitura.

* **`database-v2`**
  * **Objetivo:** Isolamento da primeira etapa da reengenharia. Modelação do novo banco, schemas, stored procedures (se aplicável) e fluxos estritos de integridade (`ON DELETE CASCADE`).
  * **Responsabilidade:** Time de Arquitetura / DBAs.

* **`backend-v2`**
  * **Objetivo:** Refatoração estrita da API. Seu trabalho é replicar integralmente o que está definido no `API_CONTRACT_FREEZE.md` e no `BUSINESS_RULES.md`, garantindo que os mesmos endpoints existam (com a mesma assinatura) mas escritos sob a nova fundação e conectado ao `database-v2`.
  * **Responsabilidade:** Time de Engenharia Backend (FastAPI / Outros).

* **`frontend-v2`**
  * **Objetivo:** Otimização visual, atualização de pacotes (Next.js App Router) e eventual migração de componentes. Durante grande parte do tempo, atuará consumindo endpoints de mock baseados nos contratos V1 congelados.
  * **Responsabilidade:** Time de Engenharia Frontend.

* **`integration-v2`**
  * **Objetivo:** Atuar como o "novo Release Candidate". É a branch onde `backend-v2`, `database-v2` e `frontend-v2` se chocam para provar que a aplicação Fim-a-Fim está funcional sem regressões em relação à versão congelada.
  * **Responsabilidade:** Tech Lead / DevOps.

---

## 2. REGRAS DE MERGE E DEPLOYMENT

1. **Separação de Domínios:** É terminantemente proibido commitar alterações de UI na `backend-v2` ou alterações de schema na `frontend-v2`. Cada squad possui um pipeline cego.
2. **Pull Requests (PR) com Prova Contratual:** O Backend só pode dar Merge para `integration-v2` se todos os testes E2E do Swagger provarem consistência com o `API_CONTRACT_FREEZE.md`.
3. **Bloqueio da Main:** Não haverá Merges de features novas para a `main`. A `main` só será atualizada quando o produto da ramificação `integration-v2` for coroado como a versão estável final de produção (v2.0.0 Release).
