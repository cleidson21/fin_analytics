# FINANALYTICS V3 — ARCHITECTURE CONTRACT
> Documento Mestre de Referência para Contratos de Domínio e API.
> Qualquer alteração arquitetural obriga a atualização de todas as camadas documentadas neste fluxo.
> Proibida a implementação "parcial" (ex: SQL Raw no Router).

## 1. Regra de Ouro (Mapeamento Obrigatório)
Toda entidade do sistema deve ser instanciada através do ciclo completo:
`Tabela (SQLite) ↓ Model (ORM) ↓ Repository ↓ DTO ↓ Endpoint ↓ Frontend ↓ Teste`

Se alguma dessas etapas estiver ausente, o contrato está quebrado e a funcionalidade deve ser classificada como Incompleta/Bug.

## 2. Contrato de Entidades

### Transactions
- **Tabela:** `transactions`
- **Model:** `Transaction` (em `backend/domains/banking/models.py`)
- **Repository:** `TransactionRepository` (em `backend/domains/banking/repository.py`)
- **DTO:** `TransactionDTO` (em `backend/domains/banking/dto.py`)
- **Endpoint:** `GET /transactions`
- **Frontend:** `TransactionsTab.tsx` (`Transaction` interface em `entities.ts`)
- **Teste:** `tests/test_transactions.py`

### Positions
- **Tabela:** `position_snapshots`
- **Model:** `PositionSnapshot` (em `backend/domains/investments/models.py`)
- **Repository:** `PositionRepository` (a implementar)
- **DTO:** `PositionSnapshotDTO` (a implementar)
- **Endpoint:** `GET /positions`
- **Frontend:** `PositionsTab.tsx`
- **Teste:** `tests/test_positions.py`

### Dividends
- **Tabela:** `dividends`
- **Model:** `Dividend` (em `backend/domains/investments/models.py`)
- **Repository:** `DividendRepository` (a implementar)
- **DTO:** `DividendDTO` (a implementar)
- **Endpoint:** `GET /dividends`
- **Frontend:** `DividendsTab.tsx`
- **Teste:** `tests/test_dividends.py`

### Import Runs
- **Tabela:** `import_runs` e `import_artifacts`
- **Model:** `ImportRun` e `ImportArtifact` (a implementar)
- **Repository:** `ImportRepository` (a implementar)
- **DTO:** `ImportRunDTO`, `ImportArtifactDTO`
- **Endpoint:** `GET /imports`, `GET /imports/{id}`
- **Frontend:** `ImportsTab.tsx`, `ReviewPage.tsx`
- **Teste:** `tests/test_imports_router.py`

## 3. Contrato de Domínio (Fluxo de Importação)
A esteira de ingestão deve respeitar estritamente o pipeline funcional abaixo, onde a saída de uma etapa é o insumo tipado da próxima:

1. **Payload (Arquivo / Texto)**
2. ↓ `Reader` (Gera string crua e metadados)
3. ↓ `Parser` (Gera `ImportArtifact` não-validado)
4. ↓ `Validator` (Gera `ValidationResult` com alertas ou erros)
5. ↓ `Normalizer` (Uniformiza strings, converte datas para ISO)
6. ↓ `Staging (SQLite)` (Salva os Artifacts com status PENDING)
7. ↓ `Classification` (Aciona LLM se aplicável)
8. ↓ `Confirm` (O usuário aciona o Endpoint e os Artifacts viram dados)
9. ↓ `Repositories` (Gravação nos agregados finais)
10. ↓ `Transaction / PositionSnapshot / Dividend / PortfolioSnapshot` (Tabelas Finais)


## 4. Princípio da Camada Única (Single Layer Principle)
Para assegurar a separação de responsabilidades e permitir a reutilização do Domínio sem quebra de contrato, as seguintes restrições são absolutas no backend:

- ❌ **Router não pode acessar banco:** O 
outer.py não pode importar engine, 	ext nem instanciar queries.
- ❌ **Front não deve conhecer schema do banco:** O Frontend só interage com o formato limpo definido nos DTOs.
- ❌ **Service não deve conhecer SQL:** Toda a linguagem SQL fica contida estritamente dentro dos Repositories.
- ❌ **Repository não deve retornar dict sujo do banco:** O Repository pode usar SQL Raw, mas os retornos devem preencher os DTOs no Service.
- ❌ **DTO não acessa banco:** DTOs são apenas Pydantic Models estáticos.

A direção obrigatória do fluxo de dados é sempre:
Frontend -> Router -> Service -> Repository -> Model -> SQLite
