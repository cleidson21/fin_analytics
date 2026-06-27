# 31 — ENTERPRISE FINDINGS
## Fase 5 — Achados da Revisão Arquitetural (Edição 2 — Deep Audit)
**Última atualização:** 2026-06-26 | **Revisão:** Enterprise Review 2 (ER2)

---

## Legenda de Severidade

| Símbolo | Significado |
|---|---|
| 🔴 CRÍTICO | Pode causar dados incorretos ou falha silenciosa |
| 🟠 ALTO | Risco estrutural confirmado para sprints futuros |
| 🟡 MÉDIO | Degradação de manutenção ou performance |
| 🟢 BAIXO | Melhoria incremental, sem urgência |
| 💡 SUGESTÃO | Boa prática, sem impacto imediato |
| ✅ RESOLVIDO | Encerrado em sprint anterior |

---

## Tabela de Achados

| ID | Sev | Componente | Descrição | Impacto | Evidência | Solução | Status |
|---|---|---|---|---|---|---|---|
| FIND-001 | ✅ | Readers | Duplicação de lógica entre `NubankContaReader` e `NubankFaturaReader`. | — | — | `BaseCsvReader` criado. | **RESOLVIDO** |
| FIND-002 | 🟡 MÉDIO | Normalizers | Heurísticas de normalização de descrição via `if/elif` hardcoded nos Normalizers. | Violação OCP. Para 5+ fontes cresce indefinidamente. | `nubank_conta.py` L13–24, `pierre_txt.py` L16–20 | Externalizar regras para dicionários em `rules/`. | **PENDENTE** |
| FIND-003 | 🟡 MÉDIO | Validators | `NubankContaValidator` itera todas as linhas em loop Python puro para validar data/valor. | Gargalo de performance para arquivos B3 com 10k+ linhas. | `validators/nubank_conta.py` L20–28 | Substituir por validação vetorizada via pandas. | **PENDENTE** |
| FIND-004 | ✅ | Parsers | `NubankFaturaParser` sem `try/except` na conversão Decimal. | — | — | Tratamento defensivo implementado com logging. | **RESOLVIDO** |
| FIND-005 | 🟢 BAIXO | Normalizers | ~30% das transações da Conta Nubank retornam `normalized_description` = `description` bruta. | Gap semântico. Dificulta categorização futura. | `V1 canonical_events.csv` — entradas sem mapeamento | Ampliar mapa de heurísticas da Conta Nubank. | **PENDENTE** |
| FIND-006 | 🟢 BAIXO | DTOs | `RawDocument.content` tipado como `Any`. | Reduz rastreabilidade em análise estática. | `dto.py` L36 | Restringir para `Union[List[Dict[str, Any]], List[str]]`. | **PENDENTE** |
| FIND-007 | 💡 | Pipelines | `Pipeline.execute()` retorna `Tuple` bruto sem estatísticas ou warnings embutidos. | Governança futura precisará de um DTO de resultado estruturado. | Todos os `pipelines/*.py` | Criar `PipelineResult` DTO. | **PENDENTE** |
| FIND-008 | ✅ | Testes | `NubankFaturaValidator` sem teste para data inválida. | — | — | `test_validator_invalid_date_fatura` criado. | **RESOLVIDO** |
| FIND-009 | 💡 | Artefatos | `render_flow.md` gerado com `↓` em UTF-8; PowerShell exibe `?` sem `-Encoding utf8`. | Cosmético — nenhum impacto funcional. | Ambos V1 e V2 `render_flow.md` | Documentar no Doc 27. | **PENDENTE** |
| FIND-010 | 🟢 BAIXO | Golden Tests | `canonical_events.csv` V1 com `normalized_description` igual à `description` bruta para ~30% dos eventos. | Gap semântico acumulado em dados. | `V1 canonical_events.csv` | Dependente de FIND-005. | **PENDENTE** |
| FIND-011 | ✅ | Readers / Pierre | `PierreTxtReader` usava `line.strip('\n')` que **não remove `\r`** em arquivos CRLF Windows. | Corrupção silenciosa de strings com `\r` residual, corrompendo match de categorias. | `readers/pierre_txt.py` L19 | `rstrip()` substituiu `strip('\n')` — corrigido em ER2. | **RESOLVIDO** |
| FIND-012 | ✅ | Parsers / Pierre | Filtro emoji `[A-Za-z0-9]` dependia da ausência de alfanúméricos em emojis. | Risco de categoria numérica tratada como descrição. | `parsers/pierre_txt.py` L71 | `_is_emoji_only_line()` via `unicodedata.category` — agnosta a qualquer emoji presente ou futuro. | **RESOLVIDO** |
| FIND-013 | ✅ | Parsers / Pierre | Categoria composta (`text_lines[1:]`) não era testada explicitamente. | Risco de categoria concatenada incorretamente. | `parsers/pierre_txt.py` L74 | `test_compound_category_two_lines` e `test_compound_category_three_lines` adicionados. Separador alterado para ` | ` (mais legível). | **RESOLVIDO** |
| FIND-014 | 🟡 MÉDIO | Normalizers / Pierre | `PierreTxtNormalizer` usa `hashlib.md5` para `external_uuid`. MD5 é fraco para hashing criptográfico (embora aqui seja apenas para identificação). Nubank Fatura já usa MD5 também. | Sem risco funcional atual, mas inconsistente com `BaseCsvReader` que usa SHA-256. | `normalizers/pierre_txt.py` L14, `normalizers/nubank_fatura.py` L14 | Padronizar tudo para SHA-256 (ou adotar UUID4 com seed determinístico). | **PENDENTE → P3** |
| FIND-015 | ✅ | Testes / Pierre | `test_pierre_pipeline.py` não possuía testes de parser para bloco com categoria composta, nem para valor negativo explícito. | Cobertura incompleta. | `test_pierre_pipeline.py` | Suíte completa de 57 testes Pierre gerada em TSK-5.R2 (total geral: 67 testes). | **RESOLVIDO** |
| FIND-016 | 🟢 BAIXO | Readers / Pierre | `PierreTxtReader` não herda de `BaseCsvReader` (por design, já que lê TXT, não CSV). Porém a lógica de hashing e construção do `RawDocument` é duplicada manualmente em relação ao `BaseCsvReader`. | Duplicação sutil entre TXT Reader e Base CSV Reader. | `pierre_txt.py` L1–34 vs `base.py` L15–41 | Criar uma `BaseReader` ainda mais genérica, deixando `BaseCsvReader` como especialização. Ou ao menos extrair `_build_document()` helper. | **PENDENTE → P3** |
