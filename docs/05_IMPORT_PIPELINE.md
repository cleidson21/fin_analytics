> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.
> Em caso de conflito entre documentos, `60_ARCHITECTURE_REVISION_V31.md` prevalece.

# 05 — Pipeline de Importação V3

**Versão:** 3.0 | **Status:** VIGENTE — Pipeline Direto | **Data:** 2026-07-30

---

## Filosofia do Pipeline

O pipeline é **único**. Não existem dois fluxos de código separados — apenas **dois modos de entrada de dados**:

```
[PROD]   Pierre API → JSON em memória ──────────────┐
[DEV]    Pierre API → exports/pierre/raw/ → memória ─┤
[REPLAY] exports/pierre/raw/<arquivo.json> → memória ─┘
                                                      │
                                                      ▼
                                           Validação simples (Pydantic)
                                                      │
                                                      ▼
                                        Accounts UPSERT (provider, external_id)
                                                      │
                                                      ▼
                                      Transactions UPSERT (provider, external_id)
                                                      │
                                                      ▼
                                        Categories INSERT OR IGNORE
                                                      │
                                                      ▼
                                       sync_state UPDATE + sync_history INSERT
```

---

## Modos de Operação

### Modo Produção (PROD)
- Chama a API Pierre diretamente
- JSON fica em memória — **não é salvo em disco**
- Executa o pipeline completo

### Modo Desenvolvimento (DEV)
- Chama a API Pierre
- Salva o JSON bruto em `exports/pierre/raw/<timestamp>.json`
- Executa o mesmo pipeline de produção sobre o JSON salvo
- Permite reprodução de bugs, testes e replay offline

### Modo Replay (REPLAY)
- Recebe o caminho de um arquivo JSON salvo anteriormente
- **Não chama a API Pierre**
- Executa o pipeline completo sobre o arquivo
- Resultado esperado: **idêntico à execução original** (idempotência comprovada)

---

## Regras do Pipeline

1. **Idempotência absoluta:** Executar 2x com o mesmo JSON = mesmo resultado, zero duplicações
2. **Nenhum campo calculado ou deduzido:** O pipeline persiste o que recebe
3. **Campos desconhecidos → `extra_json`:** Nunca falha por campos novos da API
4. **O pipeline não sabe nada sobre frontend** ou outros domínios
5. **UPSERT** em accounts e transactions — nunca INSERT puro (sem ON CONFLICT)

---

## Localização no Código

```
backend/domains/pierre/
    pipeline.py    ← lógica central do pipeline
    service.py     ← orquestra modos PROD / DEV / REPLAY
    repository.py  ← executa os UPSERTs no banco
```

---

## Referência Completa

Ver [`60_ARCHITECTURE_REVISION_V31.md`](60_ARCHITECTURE_REVISION_V31.md) — Seção 7 (Pipeline de Sincronização).
