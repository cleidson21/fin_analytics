> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# 61 — Definition of Done: Sprint 4.4 — Pierre Completo

**Sprint:** 4.4 | **Status:** 🔲 Em andamento | **Data:** 2026-07-30

---

## Checklist de Conclusão

A Sprint 4.4 é considerada **100% concluída** somente quando **todos** os itens abaixo estiverem marcados:

---

### 4.4.1 — Banco e Pipeline Base

- [ ] Models SQLAlchemy criados: `accounts`, `transactions`, `categories`, `sync_state`, `sync_history`
- [ ] Migration Alembic inicial criada e aplicada com sucesso
- [ ] Schema das tabelas corresponde 100% ao definido em [`03_DATABASE.md`](03_DATABASE.md)
- [ ] `shared/db.py` fornece Engine e Session factory
- [ ] `shared/config.py` lê todas as variáveis de `.env` necessárias
- [ ] `shared/security.py` fornece helpers JWT funcionais
- [ ] `pierre/pipeline.py` tem skeleton com os 3 modos (PROD / DEV / REPLAY) estruturados

---

### 4.4.2 — Sincronização Pierre

- [ ] Pipeline PROD: chama API Pierre, persiste em memória, executa UPSERT
- [ ] Pipeline DEV: chama API Pierre, salva JSON em `exports/pierre/raw/`, executa UPSERT
- [ ] Pipeline REPLAY: carrega JSON salvo, executa o **mesmo** pipeline sem chamar a API
- [ ] `accounts`: UPSERT idempotente funcionando (ON CONFLICT: provider + external_id)
- [ ] `transactions`: UPSERT idempotente funcionando (ON CONFLICT: provider + external_id)
- [ ] `categories`: INSERT OR IGNORE funcionando (catálogo automático)
- [ ] Campos desconhecidos da API Pierre são armazenados em `extra_json` sem falha

---

### 4.4.3 — Governança

- [ ] `sync_state` atualizado ao final de cada sincronização bem-sucedida
- [ ] `sync_history` registra every execução: SUCESSO ou FALHA com mensagem de erro
- [ ] Endpoint `GET /pierre/sync/status` retorna estado atual do `sync_state`
- [ ] Endpoint `GET /pierre/sync/history` retorna histórico paginado do `sync_history`
- [ ] Tela de Governança no frontend exibe histórico e status de sincronização

---

### 4.4.4 — Dashboard

- [ ] Dashboard consome **exclusivamente** dados do banco local (zero chamadas diretas à Pierre)
- [ ] **Nenhum dado mockado** presente no fluxo
- [ ] Visão de contas: total de contas sincronizadas, saldos por tipo (BANK / CREDIT)
- [ ] Visão de transações: total de transações, volume por categoria, timeline
- [ ] Endpoint `GET /dashboard/cashflow` funcional e documentado

---

### 4.4.5 — Teste de Replay (Idempotência)

- [ ] **Teste 1:** Sincronização inicial → N registros inseridos, 0 erros
- [ ] **Teste 2:** Re-execução com mesmo JSON (REPLAY) → 0 novos registros, 0 duplicações
- [ ] **Teste 3:** Contagem total de `accounts` antes = contagem depois do replay
- [ ] **Teste 4:** Contagem total de `transactions` antes = contagem depois do replay
- [ ] Teste automatizado (`test_sync_idempotence.py`) rodando e passando no CI

---

### Vertical Slice Completo

- [ ] Backend implementado (models, schemas, repository, service, pipeline, router)
- [ ] Banco populado com dados reais da Pierre
- [ ] API documentada (FastAPI /docs atualizado)
- [ ] Frontend exibindo dados reais sincronizados
- [ ] Testes isolados do domínio pierre passando (`domains/pierre/tests/`)
- [ ] Documentação `docs/` atualizada e coerente com a implementação

---

> [!CAUTION]
> **Critério bloqueante:** A Sprint 4.4 NÃO será considerada concluída se existir qualquer dado mockado no fluxo Pierre, qualquer duplicação comprovada no Teste de Replay, ou qualquer tela consumindo a API Pierre diretamente.
