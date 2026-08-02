> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Enumerações do Domínio (FIN Analytics)

---

## TransactionType
Classifica o tipo de movimentação.

| Valor | Descrição |
|---|---|
| `PURCHASE` | Compra de produto ou serviço |
| `TRANSFER` | Transferência entre contas |
| `INCOME` | Recebimento / salário / entrada |
| `INVESTMENT` | Aplicação financeira |
| `REFUND` | Estorno ou reembolso |
| `PIX` | Transação via Pix |
| `TED` | Transferência TED |
| `WITHDRAWAL` | Saque |
| `FEE` | Tarifa bancária |
| `INSTALLMENT` | Parcela de compra |
| `OTHER` | Outro |

---

## MovementType
Direção da movimentação.

| Valor | Descrição |
|---|---|
| `CREDIT` | Entrada de dinheiro |
| `DEBIT` | Saída de dinheiro |

---

## TransactionStatus
Estado de processamento da transação.

| Valor | Descrição |
|---|---|
| `PENDING` | Pendente / não processado |
| `CONFIRMED` | Confirmado e efetivado |
| `CANCELLED` | Cancelado / estornado |

---

## AssetType
Tipo de ativo financeiro.

| Valor | Descrição |
|---|---|
| `STOCK` | Ação (B3 ou internacional) |
| `FII` | Fundo de Investimento Imobiliário |
| `ETF` | Exchange-Traded Fund |
| `BOND` | Renda fixa (CDB, Tesouro, LCI, LCA) |
| `CRYPTO` | Criptomoeda |
| `FUND` | Fundo de investimento |
| `BDR` | Brazilian Depositary Receipt |
| `STOCK_US` | Ação americana (NYSE, NASDAQ) |
| `OTHER` | Outros ativos |

---

## AccountType
Tipo de conta financeira.

| Valor | Descrição |
|---|---|
| `BANK` | Conta bancária (corrente, poupança) |
| `CREDIT_CARD` | Cartão de crédito |
| `INVESTMENT` | Conta de investimentos / corretora |
| `LOAN` | Empréstimo ou financiamento |
| `WALLET` | Carteira digital |
| `OTHER` | Outro |

---

## IncomeType
Tipo de provento de ativos.

| Valor | Descrição |
|---|---|
| `DIVIDEND` | Dividendo |
| `JCP` | Juros sobre Capital Próprio |
| `RENT` | Aluguel (FII) |
| `INTEREST` | Juros de renda fixa |
| `AMORTIZATION` | Amortização de CRI/CRA |
| `OTHER` | Outro |

---

## ProviderType
Identificador dos Providers externos.

| Valor | Descrição |
|---|---|
| `PIERRE` | Pierre Finance (Open Finance — Banking) |
| `MYPROFIT` | MyProfit (Investimentos B3) |
| `CSV` | Importação via arquivo CSV |
| `YFINANCE` | Yahoo Finance (cotações e dados de mercado) |
| `MANUAL` | Entrada manual pelo usuário |

---

## ProviderStatus
Estado da conexão do usuário com o Provider.

| Valor | Descrição |
|---|---|
| `ACTIVE` | Conexão ativa e funcional |
| `INACTIVE` | Desconectado pelo usuário |
| `ERROR` | Erro de autenticação ou API |
| `PENDING` | Aguardando configuração inicial |

---

## SyncStatus
Estado da última sincronização.

| Valor | Descrição |
|---|---|
| `IDLE` | Aguardando próxima sincronização |
| `RUNNING` | Sincronizando agora |
| `SUCCESS` | Última sincronização bem-sucedida |
| `FAILED` | Última sincronização falhou |
| `PARTIAL` | Sincronização parcialmente completada |

---

## UserRole
Papel do usuário no sistema.

| Valor | Descrição |
|---|---|
| `ADMIN` | Acesso total |
| `VIEWER` | Somente leitura |

---

## CurrencyType
(Não confundir com `CurrencyCode` — este enum trata o tipo de moeda)

| Valor | Descrição |
|---|---|
| `FIAT` | Moeda fiduciária (BRL, USD, EUR) |
| `CRYPTO` | Criptomoeda (BTC, ETH) |
