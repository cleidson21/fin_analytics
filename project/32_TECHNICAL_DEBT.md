# 32 — TECHNICAL DEBT
## Fase 5, 6 e 7 — Catálogo de Dívidas Técnicas (Edição 3 — Sprint 7 / Gate 10.13)
**Última atualização:** 2026-07-14 | **Revisão:** Edição 3 (Reconciliação Documental R0)

---

## Status Legend
- ✅ RESOLVIDO — Tratado em sprint anterior
- 🔴 P1 CRÍTICO — Obrigatório antes da próxima sprint
- 🟠 P2 — Obrigatório antes do sprint indicado
- 🟡 P3 — Oportunístico, sem urgência imediata

---

| ID | Componente | Tipo | Risco | Prioridade | Complexidade | Status |
|---|---|---|---|---|---|---|
| TD-001 | `readers/nubank_conta.py` + `readers/nubank_fatura.py` | Duplicação estrutural | ALTO | **P1** | Baixa | ✅ **RESOLVIDO** — `BaseCsvReader` criado. |
| TD-002 | `normalizers/nubank_conta.py` + `normalizers/nubank_fatura.py` + `normalizers/pierre_txt.py` | Heurística hardcoded (`if/elif`) nos Normalizers | MÉDIO — Violação OCP. Para 5+ fontes, bloco cresce indefinidamente. | **P2 — Antes V4 (MyProfit)** | Média (3-5h) | Migrar regras para dicionários/YAML externos em `rules/`. |
| TD-003 | `validators/nubank_conta.py` | Validação linha-a-linha em loop Python puro | MÉDIO — Gargalo para B3 (10k+ linhas). | **P2 — Antes V5 (B3)** | Média (2-4h) | Substituir por validação vetorizada com pandas. |
| TD-004 | `dto.py` — `RawDocument.content: Any` | Tipagem fraca | BAIXO — Cega análise estática. | **P3** | Baixa (1h) | Restringir para `Union[List[Dict[str, Any]], List[str]]`. |
| TD-005 | Todos os `pipelines/*.py` | Retorno `Tuple` sem estatísticas estruturadas | BAIXO — Governança futura precisará de DTO de resultado. | **P3 — Antes Governança** | Média (3h) | Criar `PipelineResult` DTO. |
| TD-006 | `parsers/nubank_fatura.py` | Conversão `Decimal` sem tratamento defensivo | MÉDIO | **P1** | Baixa | ✅ **RESOLVIDO** — `try/except InvalidOperation` implementado. |
| TD-007 | `tests/unit/` | Ausência de testes de integração de `Pipeline.execute()` end-to-end | MÉDIO | **P2 — Antes V4** | Média (2-3h) | Testes de pipeline completo injetando `RawDocument` mock. |
| TD-008 | `normalizers/nubank_conta.py` | Cobertura de heurística incompleta (~30% dos eventos sem mapeamento) | MÉDIO | **P2 — Antes Reconciliação** | Alta (4-8h análise + mapeamento) | Catalogar todos padrões textuais do Nubank Conta. |
| TD-009 | `readers/pierre_txt.py` | `line.strip('\n')` não remove `\r` em arquivos CRLF puros | 🔴 CRÍTICO — Corrupção silenciosa de strings em TXT exportado no Windows | **P1** | Muito Baixa | ✅ **RESOLVIDO** — `rstrip()` aplicado em ER2. |
| TD-010 | `parsers/pierre_txt.py` | Filtro emoji `re.search(r'[A-Za-z0-9]', l)` podia tratar números em categoria como texto | ALTO — Risco latente para layouts futuros do Pierre | **P2** | Baixa | ✅ **RESOLVIDO** — `_is_emoji_only_line()` via `unicodedata.category`. |
| TD-011 | `normalizers/pierre_txt.py` + `normalizers/nubank_fatura.py` | Uso de `hashlib.md5` para `external_uuid` | MÉDIO — Inconsistente com SHA-256 usado em `BaseCsvReader`. | **P3** | Muito Baixa (30min por arquivo) | Padronizar tudo para SHA-256 (truncado se necessário). |
| TD-012 | `tests/unit/domains/imports/test_pierre_pipeline.py` | Ausência de testes para categoria composta e valor negativo explícito | BAIXO — Cobertura incompleta | **P2** | Muito Baixa | ✅ **RESOLVIDO** — 67 testes na suíte completa Pierre. |
| TD-013 | `readers/pierre_txt.py` | Duplicação de hashing/`RawDocument` em relação ao `BaseCsvReader` sem herança comum | BAIXO — Violação DRY entre TXT e CSV readers | **P3** | Baixa (2h) | Criar `BaseReader` genérica com `_build_document()` helper. |
| TD-014 | `parsers/nubank_conta.py` | (EA3-12) Parser sem try/except p/ NaN Pandas | CRÍTICO | **P1** | Baixa | ✅ **RESOLVIDO** — TSK-5.H1 |
| TD-015 | `readers/base.py` | (EA3-05) Propriedade concreta em abstração | ALTO | **P1** | Baixa | ✅ **RESOLVIDO** — TSK-5.H1 |
| TD-016 | `normalizers/nubank_fatura.py` | (EA3-20) Lógica frágil de UUID via raw_doc_id | ALTO | **P1** | Baixa | ✅ **RESOLVIDO** — TSK-5.H1 |
| TD-017 | `pipelines/*.py` | (EA3-24) Falta de isolamento de exceção em runtime | ALTO | **P1** | Baixa | ✅ **RESOLVIDO** — TSK-5.H1 |
| TD-018 | `tests/unit/` | (EA3-27) Falta de testes de robustez nos parsers | ALTO | **P1** | Média | ✅ **RESOLVIDO** — TSK-5.H1 |
| TD-019 | `CanonicalFinancialEvent` | (EA4-NEW-001) Incompatibilidade com leitura de Posições Estáticas (Snapshots) do CSV de Ativos MyProfit. | ALTO — Trava ingestão de balanços estruturais se forçado | **P2** | Alta | Suspender leitura de "Ativos". Necessita nova abstração (`PositionSnapshot`) no Core. |
| TD-020 | `domains/investments/engines/*` | (Gate 10.13) Engines financeiras (Position, Valuation, Wealth, Performance, History) rodando In-Memory, ignorando tabelas físicas do V3. Gargalo de memória e perda de histórico imutável. | CRÍTICO — Insustentável em produção | **P1 — Antes Fase 8** | Alta | ✅ **RESOLVIDO** — `ValuationRepository`, `WealthRepository`, `DividendRepository` criados. Persistência 100% no V3. (TSK-7.R1) |
| TD-021 | `domains/investments/router.py` | (Gate 10.13) 9+ endpoints requeridos pelo Frontend ausentes. | ALTO — Frontend com 404 em telas críticas | **P2 — Antes Fase 8** | Média | ✅ **RESOLVIDO** — Construídos endpoints de evolução, dividendos, e dashboard. (TSK-7.R3) |
| TD-022 | Integrações Externas | (Gate 10.13) yfinance, Banco Central (CDI/IPCA), Gemini AI, APScheduler e python-dotenv ausentes. | ALTO — Dados financeiros incorretos/mockados | **P2** | Alta | Implementar integrações conforme TSK-7.INT. |
