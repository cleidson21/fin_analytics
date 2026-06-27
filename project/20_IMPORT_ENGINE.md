# 5.8 Import Engine

## Objetivo
Orquestrador master (Facade/Workflow) do pipeline de importação. 

## Fluxo Completo Obrigatório
A orquestração deve chamar as dependências nesta exata sequência:
`Reader` -> `OCR` -> `LLM` -> `Normalizer` -> `Reconciliation` -> `Governance` -> `Database`

## Regras Atômicas
Se QUALQUER etapa do fluxo falhar ou estourar tolerância de risco, a Import Engine bloqueia o andamento e aplica o Rollback imediato no Banco.
Esta Engine orquestradora é o único componente autorizado a abrir transação de `commit` com o SQLite após a validação da Engine de Governança.
