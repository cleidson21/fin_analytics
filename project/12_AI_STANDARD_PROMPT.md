# PROMPT PADRÃO — IMPLEMENTAÇÃO, DOCUMENTAÇÃO, AUDITORIA E GOVERNANÇA (FinAnalytics V3)

Sempre que executar qualquer implementação neste projeto, considere esta regra obrigatória.

---

## 1. Antes de implementar

Antes de escrever qualquer linha de código:
* Ler toda a documentação relacionada.
* Identificar a fase atual do projeto.
* Identificar dependências.
* Identificar impactos.
* Confirmar aderência ao Master Plan.
* Confirmar aderência aos contratos do Frontend.
* Confirmar aderência ao Banco congelado.

Nunca assumir comportamento. Sempre validar.

---

## 2. Implementação

Toda implementação deve obedecer rigorosamente:
* Clean Architecture
* DDD
* SQLAlchemy Core
* Raw SQL
* SQLite congelado
* Sem alterar migrations
* Sem alterar estrutura existente
* Sem quebrar contratos

Sempre utilizar o domínio correto. Nunca misturar responsabilidades.

---

## 3. Documentação obrigatória

Ao finalizar qualquer microetapa atualizar obrigatoriamente:
* project/01_PROJECT_MASTER_PLAN.md (quando houver impacto arquitetural)
* project/02_PROJECT_CHANGELOG.md
* project/03_PHASE_STATUS.md
* project/04_CURRENT_PHASE.md
* project/06_AUDIT_LOG.md
* project/07_FRONTEND_CONTRACT.md (quando necessário)
* project/08_INVESTMENTS_CONTRACT.md (quando necessário)
* project/09_IMPLEMENTATION_QUEUE.md

Quando surgir um novo assunto estrutural criar documentação própria.
Exemplos: `10_DATA_SOURCES_CATALOG.md`, `11_DATA_IMPORT_ARCHITECTURE.md`, `12_GOVERNANCE_ENGINE.md`, etc.

Cada documento deve possuir: objetivo, arquitetura, regras, exemplos, limitações, decisões tomadas, riscos, próximos passos.

---

## 4. Auditoria

Toda implementação deve produzir uma auditoria técnica.
Registrar:
* objetivo, arquivos criados, arquivos alterados, endpoints criados
* DTOs criados, repositories criados, services criados, queries SQL criadas
* migrations alteradas (esperado: nenhuma)
* impacto arquitetural, impacto de performance
* dependências externas adicionadas
* riscos encontrados, divergências encontradas, decisões tomadas
* compatibilidade com versões anteriores

---

## 5. Logs

Atualizar:
* **CHANGELOG:** funcionalidades, correções, melhorias, refatorações.
* **AUDIT_LOG:** justificativa, motivo técnico, motivo arquitetural, impactos.
* **CURRENT_PHASE:** andamento da fase.
* **PHASE_STATUS:** progresso geral.
* **IMPLEMENTATION_QUEUE:** Marcar COMPLETED, IN PROGRESS, BLOCKED.

---

## 6. Testes obrigatórios

Executar sempre que possível:
* testes unitários, testes de integração, testes E2E, testes SQL
* validação dos DTOs, contratos e rotas.
Quando não puder executar: explicar claramente o motivo.

---

## 7. Banco congelado

É proibido: alterar migrations, alterar schema, remover tabelas, modificar constraints, modificar índices.
Qualquer necessidade deverá ser documentada, nunca implementada automaticamente.

---

## 8. Uso de bibliotecas externas

Antes de implementar qualquer nova funcionalidade, verificar se já existe uma biblioteca madura, projeto open source consolidado ou API oficial que resolva o problema. Só desenvolver código proprietário quando isso representar o diferencial competitivo do FinAnalytics.

Prioridade de uso maduro antes de criar parser do zero: OCR (PaddleOCR, Tesseract), PDF (pdfplumber, PyMuPDF, camelot-py), Planilhas (pandas, openpyxl), Embeddings (FAISS), Contábil (beancount).
Sempre justificar vantagens, desvantagens, licença, e facilidade de integração. Nunca adicionar sem documentar.

---

## 9. Engenharia de IA

Não desenvolver modelos próprios inicialmente. Usar OpenAI para classificação, OCR difícil, parser textual, etc.
Guardar conhecimento em embeddings. Registrar toda decisão.

---

## 10. Camada de Importação

Fluxo obrigatório: Readers -> Validators -> Normalizers -> Canonical Financial Event -> Reconcilers -> Governance -> Import Engine -> Rollback/Commit. Nenhum parser pode escrever diretamente no banco.

---

## 11. Canonical Financial Event

Todo dado importado deve ser convertido primeiro para um modelo canônico.

---

## 12. Governança

Fluxo obrigatório: ImportSession -> ImportBatch -> ImportRun -> Validation -> Conflict Detection -> Commit/Rollback.
Registrar: `run_id`, `source_system`, `external_hash`, `external_uuid`, `raw_data`, `import_statistics`.

---

## 13. Relatório Final Obrigatório

Toda microetapa deve terminar produzindo:
1. Objetivo executado
2. Arquivos criados
3. Arquivos alterados
4. Endpoints criados
5. Queries implementadas
6. Testes executados
7. Evidências encontradas
8. Divergências encontradas
9. Impacto arquitetural
10. Atualizações dos logs
11. Confirmação do Freeze
12. Próxima microetapa sugerida
13. Parecer técnico

Finalizar com MICROETAPA CONCLUÍDA ou FASE CERTIFICADA.

---

## 14. Filosofia do Projeto

Antes de escrever código: pensar na arquitetura.
Antes de implementar: pensar na governança.
Antes de persistir: pensar na reconciliação.
Antes de importar: pensar na deduplicação.
Antes de usar IA: pensar na rastreabilidade.
Toda decisão deve ser reproduzível, auditável, reversível e documentada.
