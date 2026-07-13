# DB Consistency Audit (Gate 4.5)

## 1. Escopo da Auditoria
Conforme estabelecido pela Etapa Final de leitura do banco e do plano de implementação, esta auditoria tem o objetivo de atestar o impacto e a aderência da infraestrutura de banco de dados para a Sprint 3C.2 (CEI Trades).

## 2. Leitura de Schema e Descoberta Arquitetural
Durante a leitura meticulosa dos arquivos em `database/migrations/` (de 001 a 013), constatou-se a seguinte situação na **migration 004_investments.sql**:

**Evidência Encontrada:** A tabela `trades` **JÁ EXISTE** fisicamente na migration `004`.
Ela está plenamente mapeada com:
- `asset_id` (FK para `assets.id`)
- `account_id` (FK para `accounts.id`)
- `type` (`BUY` e `SELL`)
- `gross_value`, `net_value` (Calculados por engine geradora do SQLite)
- `source` (Previsão de regra de domínio contendo explícito o enum `'B3_API'`).

## 3. Impactos, Compatibilidade e Conflitos
- **Impacto Sistêmico:** Criar a tabela proposta `014_cei_trades.sql` geraria uma anomalia severa no banco. Haveria duas fontes da verdade para negociações (`trades` e `cei_trades`).
- **Position Engine / Snapshot Engine / Performance (MWR/TWR):** Todas essas engines legadas (desenhadas entre a Fase 1 e 2) já apontam nativamente e consomem dados da tabela genérica `trades`.
- **Risco Mitigado:** O Gate de Leitura do Schema impediu a duplicação. Nenhuma tabela, FK ou regra de negócio foi ou será quebrada, pois nós **reaproveitaremos 100%** a estrutura nativa.

## 4. Aprovação e Diretriz de Criação (CONCLUSÃO OBRIGATÓRIA)
**DECISÃO:** A criação do arquivo `014_cei_trades.sql` está **VETADA**, bem como qualquer nova migration para esta funcionalidade.

**Ação Técnica:** O backend do projeto (Domain `investments`) apenas instanciará o `TradeRepository` em cima da tabela `trades` já existente e fará a ingestão dos dados CEI direcionando o campo `source` para `'B3_API'`.

*Esta decisão mantém o banco imaculado, previne refatorações perigosas nas engines de cálculo e consolida a universalidade do Ledger V3.*
