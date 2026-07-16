# 35. Arquitetura da Inteligência Artificial (Gemini)

Este documento define a arquitetura da camada de Inteligência Artificial do FINANALYTICS V3 (Fase 8), garantindo que os LLMs operem de forma segura, governada e puramente consultiva, sem violar as regras de negócio dos domínios financeiros existentes.

## 1. Objetivos da IA

A Inteligência Artificial atuará de forma analítica e passiva, focada na extração de insights, simplificação de dados e tomada de decisão informada para o usuário. Suas responsabilidades diretas incluem:
- **Interpretação e Classificação:** Analisar descritivos obscuros de lançamentos e faturas e sugerir categorizações semânticas (ex: "Pgto Uber" -> "Transporte").
- **Geração de Insights de Carteira:** Avaliar a diversificação atual (Allocation) e risco em cima dos dados provenientes da `FinancialAnalyticsEngine`.
- **Análise Patrimonial:** Avaliar a rentabilidade histórica do usuário frente aos benchmarks macroeconômicos (CDI, SELIC, IPCA, IBOV).
- **Extração via OCR/Documentos:** Interpretação de notas de corretagem ou PDFs bancários formatando o conteúdo para o pipeline de importação estruturada (ETL).

## 2. Limites (Guardrails)

A IA está explicitamente restrita às seguintes barreiras arquiteturais:
- **Somente Leitura (Read-Only AI):** A IA NUNCA poderá executar inserções, atualizações ou exclusões no banco de dados (`INSERT`, `UPDATE`, `DELETE`).
- **Isolamento de Engines:** A IA NUNCA fará cálculos financeiros pesados. Toda precificação, PNL, amortização e split será delegada às Engines Oficiais.
- **Não-Transacional:** A IA NUNCA iniciará transações financeiras (Open Finance) ou autorizações de pagamentos.
- **Camada Consultiva:** A IA entregará `Sugestões` e `DTOs de Interpretação`. A efetivação dessas sugestões dependerá exclusivamente dos Services transacionais.

## 3. Arquitetura do Domínio (`backend/domains/ai/`)

A estrutura adotará Padrões de Projeto (Design Patterns) aderentes à Clean Architecture, isolando lógicas de prompt, comunicação de rede e modelos de resposta.

```text
backend/domains/ai/
├── interfaces.py          # LLMProvider (Interface Base)
├── models.py              # DTOs de Entrada e Saída (ex: AIInsightDTO, AICategorizationDTO)
├── providers/
│   ├── base.py            # Classe Abstrata LLM
│   └── gemini.py          # Implementação oficial Google Gemini API
├── prompts/
│   ├── templates.py       # Centralização de Prompts (Zero-shot, Few-shot)
│   └── formatters.py      # Injetores de contexto JSON no template
├── orchestration/
│   └── agent_service.py   # Orquestra chamadas, cache e parse de respostas
├── tools/
│   └── function_calls.py  # Mapeamento estrito de Function Calling (Read-only)
└── router.py              # Endpoints FastAPI para interagir com a UI de IA
```

## 4. Integração

A integração da IA obedecerá ao princípio da inversão de dependências, consumindo dados consolidados em vez de acessar tabelas cruas:
- **Dashboard / Engines:** A IA consumirá as visões materializadas (Read Models) e saídas do `PortfolioApplicationService` e `MarketDataService`.
- **ETL (Importadores):** O `PierreTxtNormalizer` e futuros extratores delegarão `raw_text` para a camada de IA via injeção de dependência (`AIExtractionService`).
- **Market Data:** Contexto econômico (CDI diário, IPCA) será apensado aos Prompts via chamadas locais à API de Market Data para que a IA justifique recomendações com embasamento fático atual.
- **Banco de Dados:** A IA **não** terá acesso a `Session` do SQLAlchemy para escrita.

## 5. Segurança

- **Gerenciamento de API Key:** Armazenada estritamente em `.env` (`GEMINI_API_KEY`). Nenhuma chave transitará no frontend.
- **Tratamento de Erros & Fallback:** Respostas da API do LLM serão envelopadas em blocos `try/except` monitorados. Em caso de timeout (> 15s) ou `HTTP 429` (Quota Exceeded), a aplicação ativará o padrão `Circuit Breaker`, retornando _Fallbacks_ semânticos vazios para não bloquear a experiência do usuário.
- **Sanitização:** Todo _output_ json da IA passará pelo Pydantic para validação rigorosa dos tipos, prevenindo alucinações de formato.

## 6. Custos e Otimização

- **Redução de Tokens:** Os dados (ex: histórico de trades) serão agregados, truncados ou sumarizados pelo Backend Clássico **antes** de entrarem no prompt da IA, evitando desperdício de Context Window.
- **Cache de Respostas:** Perguntas e análises idênticas para a mesma janela de D-1 utilizarão Cache Semântico ou `Redis`/Memória (TTL de 24h para análises estáticas de portfólio) a fim de poupar tokens duplicados.
- **Batching:** Avaliações de categorização de gastos bancários serão feitas em lotes (arrays de 50 descrições) via 1 única requisição em vez de 50 requisições isoladas.

## 7. Governança e Rastreabilidade

- **Auditoria de Prompts:** Todo _prompt_ possuirá versão atrelada (ex: `V1_PORTFOLIO_ANALYSIS`). Mudanças nos templates serão tratadas como mudanças de código-fonte (Pull Request / Audit Log).
- **Rastreabilidade de Respostas:** Será criada uma tabela de log `ai_audit_log` (opcional em futuras sub-tasks) que registrará o Request Hash, Token Count, Response Time e ID do Modelo para depuração em caso de anomalias regulatórias.
