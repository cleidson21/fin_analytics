# SPRINT H1 — CONSOLIDAÇÃO ARQUITETURAL E CONTRATOS

> **Objetivo:** Estabelecer a fonte da verdade definitiva (Banco SQLite), mapear e ajustar a rastreabilidade Banco → Front, documentar os pipelines de importação reais, e pautar a homologação com testes automatizados. O objetivo não é criar funcionalidades.

## H1.1 Contrato do Banco
O Banco SQLite é a FONTE ÚNICA DA VERDADE. O _schema_ completo possui as tabelas, FKs, constraints UNIQUE, constraints CHECK e índices perfeitamente definidos. Nenhuma coluna deve ser gerada sob demanda; as migrations são a única fonte de mutação estrutural.

## H1.2 Contrato ORM
Matriz de rastreabilidade (Tabela SQLite ↓ Model ORM ↓ Repository ↓ DTO ↓ Router ↓ Frontend):

* **Transactions**: `transactions` ↓ `Transaction` ↓ `TransactionRepository` ↓ `TransactionDTO` ↓ `GET /transactions` ↓ `TransactionsTab.tsx`. **Status:** ⏳ Apresenta cobertura arquitetural superior às demais entidades, porém ainda depende da auditoria H1 para homologação definitiva (CRUD, filtros, paginação, testes E2E).
* **Positions**: `position_snapshots` ↓ `PositionSnapshot` ↓ Falta Repository ↓ Falta DTO ↓ `GET /positions` ↓ `PositionsTab.tsx`. **Status:** ✖ SQL Raw presente diretamente no Router. Quebra arquitetural a ser corrigida na H1.
* **Dividends**: `dividends` ↓ `Dividend` ↓ Falta Repository ↓ Falta DTO ↓ `GET /dividends` ↓ `DividendsTab.tsx`. **Status:** ✖ SQL Raw presente diretamente no Router. Quebra arquitetural a ser corrigida na H1.

## H1.3 Contrato Front
Matriz de Homologação:

| Tela | Endpoint | DTO | Banco | Status |
|---|---|---|---|---|
| Dashboard | ✔ | ✔ | ✔ | OK |
| Imports | ✔ | ✖ | ✔ | Ajustar |
| Transactions| ✔ | ✔ | ✔ | OK (Carece E2E final) |
| Positions | ✔ | ✖ | ✔ | Ajustar |
| Dividends | ✔ | ✖ | ✔ | Ajustar |

## H1.4 Inventário de Importadores (Maturidade)
O processo atual encontra-se com parsers temporários centralizados (`confirm_and_process`). O pipeline alvo deve seguir a esteira exata.

| Etapa | Nubank | Pierre | B3 | MyProfit |
|---|---|---|---|---|
| Reader | ✔ | ✔ | ✔ | ✔ |
| Detect Source | ✔ | ✔ | ✔ | ✔ |
| Decode | ✔ | ✔ | ✖ | ✔ |
| Parse | ✔ | ✔ | ▲ | ✔ |
| Normalize | ✖ | ✖ | ✖ | ✖ |
| Validate | ✖ | ✖ | ✖ | ✖ |
| Preview | ▲ | ▲ | ▲ | ▲ |
| Confirm | ✔ | ✔ | ✔ | ✔ |
| Rollback | ▲ | ▲ | ▲ | ▲ |

Legenda: ✔ completo, ▲ parcial, ✖ inexistente

## H1.5 Testes
Criação e execução de testes reais com Pytest e E2E Playwright. Lista requerida (tests/):
- `test_import_nubank.py`
- `test_import_b3.py`
- `test_import_pierre.py`
- `test_import_myprofit.py`
- `test_dashboard.py`
- `test_transactions.py`
- `test_positions.py`

## H1.6 Contrato de Domínio
O pipeline de objetos transitará pelas seguintes abstrações lógicas a fim de distribuir responsabilidades:
`Importação` ↓ `Artifact` ↓ `ValidationResult` ↓ `NormalizedData` ↓ `Transaction / Position / Dividend / PortfolioSnapshot`

## H1.7 Fluxograma Ponta a Ponta
O fluxo de ingestão respeitará o seguinte roteiro síncrono e unificado:
`Frontend` ↓ `POST Upload` ↓ `Router` ↓ `ImportService` ↓ `Reader` ↓ `Parser` ↓ `Validation` ↓ `Classification` ↓ `Preview` ↓ `Confirm` ↓ `Repositories` ↓ `SQLite`
