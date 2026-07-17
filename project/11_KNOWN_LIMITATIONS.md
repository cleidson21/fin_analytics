# FINANALYTICS V3 — KNOWN LIMITATIONS
> Registro oficial das limitações arquiteturais inerentes à versão 3.0.0.

## 1. Single User Architecture
O FINANALYTICS V3 foi construído intencionalmente como uma plataforma `Single User Personal Financial Platform`. Não há suporte para:
- Múltiplos usuários no mesmo banco de dados.
- Autenticação avançada OAuth de terceiros (o sistema usa autenticação semente no `.env` para proteger a API).
- Separação de tenants (Multi-tenant).

## 2. Ingestão de Dados Manual-First
- Não há integração direta com Open Banking / Open Finance automatizada por API.
- Toda ingestão depende de upload manual de arquivos CSV/TXT extraídos previamente (B3, Corretoras, MyProfit, Faturas e Extratos bancários).
- A automação de dados externos se restringe apenas ao Market Data (Yahoo Finance) e Macro Indicadores (Banco Central SGS).

## 3. Inteligência Artificial (Limites Generativos)
- A IA do Gemini é operada estritamente no formato *Read-Only*. Ela não tem capacidade agêntica de movimentar dinheiro, sugerir compras e vendas com tickers literais, nem apagar registros do banco de dados.
- Falhas de infraestrutura do Google (API limits, Rate limits) causarão suspensão temporária dos serviços do módulo `ai/` sem derrubar a plataforma financeira core (que possui fallback estrito e tratamento de exceções do Provider).
- A acurácia das inferências de "Personalização" ou "Plano de Ação" não se sobrepõem ao parecer de um consultor financeiro humano real.

## 4. Integrações Não Disponíveis
- Não há aplicativo Mobile nativo independente. O sistema é voltado para navegadores desktop e móveis adaptativos (PWA-like).
- Não há entrega automática de alertas via WhatsApp ou E-mail. Todo o conteúdo gerado deve ser consumido na tela da Dashboard (entregue pelo Dashboard Delivery Layer).

## 5. Cotações e Market Data
- A integração com `yfinance` sofre de latência natural da plataforma gratuita. Em picos de uso extremo as atualizações diárias demoram mais que conectores pagos como Bloomberg ou B3 Direto. Falsos-positivos na cotação de fim-de-semana são ignorados (mantido último preço de fechamento).
