# 33 — REFACTOR QUEUE
## Fase 5 — Fila Oficial de Refatorações (Edição 2 — Deep Audit)
**Última atualização:** 2026-06-26 | **Revisão:** Enterprise Review 2

Prioridade: P1 = Obrigatório antes da próxima Sprint | P2 = Obrigatório antes do sprint indicado | P3 = Oportunístico

---

| ID | Sprint | Componente | Motivo | Impacto | Dep. | Prioridade | Esforço | Status |
|---|---|---|---|---|---|---|---|---|
| REF-001 | ~~Antes V3~~ | `readers/base.py` | Eliminar duplicação entre readers CSV. | Alto | — | **P1** | 2h | ✅ **RESOLVIDO** |
| REF-002 | ~~Antes V3~~ | `readers/nubank_conta.py` + `fatura.py` | Herdar `BaseCsvReader`. | Alto | REF-001 | **P1** | 1h | ✅ **RESOLVIDO** |
| REF-003 | ~~Antes V3~~ | `parsers/nubank_fatura.py` | `try/except` defensivo no Decimal. | Médio | — | **P1** | 30min | ✅ **RESOLVIDO** |
| REF-004 | ~~Antes V3~~ | `tests/.../test_nubank_fatura_pipeline.py` | Adicionar `test_validator_invalid_date_fatura`. | Baixo | — | **P1** | 30min | ✅ **RESOLVIDO** |
| REF-005 | Antes V5 (B3) | `validators/nubank_conta.py` | Substituir loop Python por validação vetorizada pandas. | Médio (performance B3) | — | **P2** | 2-3h | PENDENTE |
| REF-006 | Antes V4 (MyProfit) | `normalizers/nubank_conta.py` | Externalizar mapeamento de descrições para `rules/`. | Médio (OCP) | — | **P2** | 4-6h | PENDENTE |
| REF-007 | Antes Governança | Todos `pipelines/*.py` | Criar `PipelineResult` DTO. | Médio (fundação Governança) | REF-001 | **P2** | 3h | PENDENTE |
| REF-008 | Oportunístico | `dto.py` `RawDocument.content` | Restringir tipo `Any` para Union tipada. | Baixo | — | **P3** | 15min | PENDENTE |
| **REF-009** | ~~Antes V4~~ | `readers/pierre_txt.py` L19 | **`strip('\n')` → `rstrip()`** para corrigir CRLF residual. | 🔴 CRÍTICO — corrupção silenciosa em TXT Windows | — | **P1** | 5min | ✅ **RESOLVIDO** |
| **REF-010** | ~~Antes V4~~ | `parsers/pierre_txt.py` | Reescrita completa com abordagem estrutural (`_is_emoji_only_line` via `unicodedata.category`). | Alto — risco latente eliminado | REF-009 | **P2** | 1h | ✅ **RESOLVIDO** |
| **REF-011** | ~~Antes V4~~ | `tests/.../test_pierre_pipeline.py` | 67 testes: validator, emoji filter, parser (happy path, edge cases, encoding), normalizer. | Cobertura completa | REF-009 | **P2** | 2h | ✅ **RESOLVIDO** |
| **REF-012** | Oportunístico | `normalizers/pierre_txt.py` + `nubank_fatura.py` | Migrar `md5` → `sha256` para `external_uuid`. | Baixo — inconsistência de padrão | — | **P3** | 30min | **PENDENTE** |
| **REF-013** | Oportunístico | `readers/pierre_txt.py` | Criar `BaseReader` genérica ou extrair `_build_document()` helper. | Baixo — DRY | REF-009 | **P3** | 2h | **PENDENTE** |
| **REF-014** | ~~Antes V4~~ | `parsers/nubank_conta.py` | EA3-12: Adicionar try/except defensivo p/ Pandas NaN. | CRÍTICO | — | **P1** | 10min | ✅ **RESOLVIDO** |
| **REF-015** | ~~Antes V4~~ | `readers/base.py` | EA3-05: Transformar `source_system` em prop abstrata. | Alto | — | **P1** | 5min | ✅ **RESOLVIDO** |
| **REF-016** | ~~Antes V4~~ | `normalizers/nubank_fatura.py` | EA3-20: Remover `raw_doc_id` do MD5 UUID. | Alto | — | **P1** | 5min | ✅ **RESOLVIDO** |
| **REF-017** | ~~Antes V4~~ | `pipelines/*.py` | EA3-24: try/except abrangente em `execute()`. | Alto | — | **P1** | 15min | ✅ **RESOLVIDO** |
| **REF-018** | ~~Antes V4~~ | `tests/unit/` | EA3-27: Testes de robustez p/ parsers (nan/invalid). | Alto | — | **P1** | 30min | ✅ **RESOLVIDO** |

---

## Itens P2/P3 Pendentes (Antes da Sprint V5/V6)

| ID | Ação | Arquivo | Esforço |
|---|---|---|---|
| REF-005 | Validação vetorizada pandas no NubankContaValidator | `validators/nubank_conta.py` | 2-3h |
| REF-006 | Externalizar heurísticas de descrição para `rules/` | `normalizers/nubank_conta.py` | 4-6h |
| REF-007 | Criar `PipelineResult` DTO | Todos `pipelines/*.py` | 3h |
| REF-012 | Migrar MD5 → SHA-256 nos `external_uuid` | `normalizers/pierre_txt.py` + `nubank_fatura.py` | 30min |
| REF-013 | Criar `BaseReader` genérica | `readers/pierre_txt.py` | 2h |
