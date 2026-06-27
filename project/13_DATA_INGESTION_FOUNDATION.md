# 5.1 Foundation

## Objetivo
Criar a base arquitetural que será utilizada por todos os parsers e importadores, antes de importar qualquer coisa real.

## Arquitetura
Criar `domains/imports/` com `dto.py`, `repository.py`, `router.py`, `services.py`.
As entidades fundamentais são:
- ImportRun
- ImportBatch
- ImportSession
- ImportAudit
- CanonicalFinancialEvent

## Regras
Nenhuma regra de negócio de parsing entra aqui. Apenas a fundação estrutural para sustentar as tabelas.
