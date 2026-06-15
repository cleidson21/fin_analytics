# MERGE POLICY - FASE 10.2

Regras absolutas de contribuição de código (Pull Requests) para garantir proteção inquebrável ao histórico original durante o processo de reconstrução do Fin Analytics.

---

## 1. REGRAS GERAIS DE BRANCHING
* O desenvolvimento direto de *features* é estritamente proibido nas branches `main` e `develop-v2`.
* As squads devem trabalhar ramificadas a partir da sua respectiva branch macro (`database-v2`, `backend-v2`, `frontend-v2`). Exemplo: `feat/backend-v2-auth`.

## 2. POLÍTICA DE DESTINO E INTEGRAÇÃO (O FUNIL)

A mescla do trabalho obedece ao seguinte funil unidirecional:

### Nível 1: As Especializadas
As branches arquiteturais atuam de forma isolada, agrupando todo o escopo antes da montagem.
* Todo o schema e governança de dados deve transitar apenas de e para **`database-v2`**.
* Toda a API FastAPI, IA e Services trafegam para **`backend-v2`**.
* Toda a reestruturação Next.js (UI/Hooks) transita para **`frontend-v2`**.

### Nível 2: O Choque (`develop-v2`)
* A branch `develop-v2` é o ponto focal e arena de teste.
* Os fluxos de mescla autorizados (Pull Requests Integrados) em ordem de cronograma são:
  * `database-v2`  ↓  `develop-v2`
  * `backend-v2`  ↓  `develop-v2`
  * `frontend-v2`  ↓  `develop-v2`

### Nível 3: Produção Congelada (`main`)
* NENHUMA branch de desenvolvimento tem permissão para fazer merge direto com a `main`. Nem mesmo a de backend ou front-end.
* O ÚNICO merge autorizado a tocar a raiz imutável do sistema é:
  * `develop-v2` ↓ `main` *(Apenas mediante aprovação total na Fase 6 de Certificação do Pipeline)*.

## 3. O ARQUIVO INTOCÁVEL
* A branch **`legacy-v1`** está em Lockdown absoluto (Read-Only). 
* Nenhum PR poderá ter esta branch como "Target" de Merge. Ela serve apenas como cápsula do tempo arqueológica para o MVP original, sendo autorizada a realizar "Checkout" para estudos de código velho.
