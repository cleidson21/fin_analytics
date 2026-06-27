# 5.7 Governance

## Objetivo
Garantir que a ingestão de dados seja controlada, auditável e reversível, protegendo a base de dados de envenenamento e lixo estatístico.

## Arquitetura
Este módulo controla os ciclos de vida e fornece ferramentas para a UI de Governança:
- **ImportRun:** O job principal de ingestão atômica.
- **Rollback:** Procedimento de exclusão em cascata pelo `run_id` no caso de rejeição de conflitos.
- **Audit:** Tracker de quem importou, o que, quando e com quais erros.
- **Logs / Warnings / Conflicts / Statistics:** Tabelas secundárias para mostrar ao usuário um resumo da ingestão (ex: 500 inseridas, 20 atualizadas, 5 com warning).

## Regras
Módulo responsável exclusivo por aprovar (Commit) ou rejeitar (Rollback) que uma importação toque definitivamente o banco de dados oficial V3.
