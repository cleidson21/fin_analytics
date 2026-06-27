# CANONICAL FINANCIAL EVENT (O Coração do Sistema)

Todos os Readers (Parsers Iniciais) do FinAnalytics dependem indiretamente desta estrutura. Nenhuma origem externa escreve diretamente em tabelas. Tudo deve ser normalizado para este formato primeiro.

## Definição (DTO)

```python
class CanonicalFinancialEvent(BaseModel):
    # Identidade
    canonical_id: str         # Hash/UUID unificador do evento (Para deduplicação)
    external_uuid: str | None # UUID oficial do banco (se existir)
    
    # Origens
    source_system: str        # Ex: "NUBANK", "B3", "PIERRE"
    import_run_id: str        # FK obrigatória do processo que o ingeriu
    raw_document_id: str      # FK para a abstração original de onde saiu
    
    # Dados Nucleares
    type: EventTypeEnum       # CASH_FLOW, TRADE, DIVIDEND, CREDIT_EXPENSE
    date: date                # Data efetiva de compensação
    description: str          # Descrição crua ou normalizada
    amount: Decimal           # Valor financeiro exato
    currency: str             # Moeda ISO 4217 (BRL, USD)
    
    # Contexto de Investimentos
    asset_ticker: str | None  # Ex: "PETR4", "KNCR11"
    quantity: Decimal | None  # Frações ou inteiros
    fees: Decimal | None      # Taxas pagas (B3, IOF)
    broker: str | None        # Ex: "NUINVEST"
    
    # Contexto de Tesouraria
    account_id: str | None    # Chave da Conta/Caixa
    credit_card_id: str | None# Chave do Cartão
    
    # Aprendizado de Máquina
    inferred_category: str | None # Classificação recebida (Ex: do Pierre)
    confidence: float             # Nível de confiança da IA
    
    # Recuperação
    raw_payload: dict         # A linha completa do CSV/JSON/TXT original
```

## Versionamento e Hash
- **Regra do Hash Canônico:** Se o documento não fornecer um `external_uuid` blindado, o `canonical_id` DEVE ser o SHA256 estrito de: `source_system` + `date` + `amount` + `account_id/broker` + substr(`description`).
- Se houver colisão de Hash, o sistema entende como **Evento Duplicado** ou **Atualização/Complemento**, engatilhando o Merge da Reconciliation Engine.

## Validações
O DTO bloqueia automaticamente:
- Valores monetários sem `currency`.
- Tipos `TRADE` sem `asset_ticker` e `quantity`.
- Tipos `CREDIT_EXPENSE` sem apontamento para `credit_card_id`.
