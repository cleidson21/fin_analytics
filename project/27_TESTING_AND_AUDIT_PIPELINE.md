# TESTING AND AUDIT PIPELINE (DATA INGESTION)

A ingestão de dados financeiros é extremamente sensível e exige prova matemática e visual antes de tocar na persistência. A partir da Fase 5 (Sprints Verticais), adotamos uma política rigorosa de **4 Níveis de Auditoria**.

Nenhum importador avança de fase sem gerar o pacote probatório obrigatório.

---

## Nível 1 — Testes Unitários
Foco em componentes isolados (TDD clássico).
- **Escopo:** DTOs, Validators, Repositories stubs, Services, Reconciliation (regras mockadas), Governança.
- **Ferramenta:** `pytest` em `tests/unit/`.
- **Objetivo:** Garantir integridade do código Python.

---

## Nível 2 — Teste Funcional (Real Samples)
Foco na execução real do pipeline End-to-End usando os arquivos brutos homologados em `samples/`.
- **Escopo:** Todo o ciclo: `Reader -> RawDocument -> Normalizer -> CanonicalFinancialEvent`.
- **Output:** Geração de um pacote probatório dentro do diretório `tests/results/V{X}_{Nome_do_Sprint}/`.

**Artefatos Gerados (Obrigatórios):**
1. `raw_document.json`: O dict bruto gerado pelo Reader.
2. `canonical_events.json`: A lista final de DTOs normalizados.
3. `import_statistics.json`: Contagem (Linhas lidas, Eventos criados, descartados, erros, conflitos).
4. `warnings.txt`: Avisos de parser não impeditivos.
5. `audit_report.md`: Resumo legível do que ocorreu na importação.

---

## Nível 3 — Teste Visual (Golden Test)
Foco em legibilidade humana. Permite que um contador, stakeholder ou o próprio usuário verifique a semântica de negócio sem usar banco de dados.
- **Artefato Gerado:** `canonical_events.csv`
- **Utilidade:** Abrir no Excel para bater visualmente:
  * Exemplo: `Date | Description | Amount | Event Type | Category`
  * Exemplo: `02/05 | PIX João | -50 | TRANSFER | null`

---

## Nível 4 — Fluxograma de Execução (Traceability)
Foco em rastreabilidade sistêmica. Como um Request Tracer, ele salva a jornada do arquivo.
- **Artefato Gerado:** `pipeline.txt`
- **Conteúdo:** Diagrama de fluxo atestando por onde o dado passou e se o *Commit* final na base oficial foi **Autorizado** ou **Bloqueado** (e o motivo exato, ex: *Conflito de saldo - Diferença: R$ 13,42*).

---

## Extensões Futuras (OCR & AI)

Quando as camadas visuais e gerativas entrarem nos sprints:

**Auditoria OCR:**
- `ocr_result.png`: Imagem cortada avaliada.
- `ocr_text.txt`: Texto bruto extraído (pixels para string).
- `ocr_corrected.txt`: Correções heurísticas antes de enviar ao normalizador.

**Auditoria OpenAI (LLM):**
- `ai_logs.md`: Motivo de acionamento (Ex: *Regex falhou*), Modelo (*gpt-4o*), Tokens gastos, Tempo (s) e Confiança.

**Auditoria Learning Engine (FAISS):**
- `learning_report.md`: Relatório de novos exemplos aprendidos e precisão estimada.

---

## Conclusão
Ao final de cada microetapa (Sprints V1 a V7), o sistema deve gerar evidências físicas e concretas nos formatos CSV, JSON, TXT e MD dentro da pasta `tests/results/`. A aprovação do Gate fica condicionada à conferência destas evidências, e não apenas a uma frase "testes passaram".
