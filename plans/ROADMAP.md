# fin_analytics_v2 — Roadmap (Business Value Expansion)

> Documento vivo. Atualizado para o ciclo de Geração de Valor (Fase 10+).
> Legenda: ✅ Concluído · 🚀 Gera Valor Imediato · ⏳ Adiado / Futuro

A arquitetura atual (Services, Repositories, Observability, Unit Tests e Pydantic Schemas) foi declarada como ESTÁVEL. Não faremos mais refatorações estruturais ou quebras de contrato. O foco exclusivo passa a ser: **Inteligência Financeira e Geração de Valor**.

---

## 🏗️ 1. Infraestrutura & Arquitetura (Estável)
Toda a base do sistema já foi construída, testada e estabilizada.

| Item | Status | Detalhes |
|---|---|---|
| Módulos Core (Controle, Wealth, Governança) | ✅ Concluído | Todos os CRUDs operando na arquitetura limpa. |
| Separação de Bancos (Financial vs Governance) | ✅ Concluído | Camadas isoladas sem vazamento de escopo. |
| Telemetria e Segurança (Observability) | ✅ Concluído | Log estruturado e métricas por Service/Repo. |
| Test Coverage (>70%) e Mocks | ✅ Concluído | Testes de unidade e contratos sem acoplar o banco. |
| Backup e Restore | ⏳ Adiado | Será executado na esteira de Operação/Deploy. |

---

## 💎 2. Produto: Business Value & Inteligência Financeira
Onde o sistema deixa de ser "descritivo" e passa a ser "prescritivo/preditivo", focando no usuário. Utiliza 100% dos dados já armazenados.

| Item | Prioridade / Status | Detalhes |
|---|---|---|
| Rebalanceamento de Carteira | 🚀 Valor Imediato | Serviço que lê as posições e indica onde aportar baseado em pesos ideais. |
| Projeção de Dividendos e Yield on Cost | 🚀 Valor Imediato | Predição de passivos usando médias móveis e YOC. |
| Concentração e Análise de Risco | 🚀 Valor Imediato | Alerta para ativos super-representados (ex: >15% num único FII). |
| Metas Financeiras (Goal Planning) | ⏳ Planejado | Nova estrutura para planejamento de independência financeira e reservas. |
| Insights Automáticos & Heurísticas | ⏳ Planejado | Análise comportamental de gastos vs orçamentos, alertas de anomalias. |

---

## 🧠 3. Inteligência Artificial (IA)
Automação e redução de atrito utilizando os metadados de governança (Prompt Versions, AI Runs).

| Item | Prioridade / Status | Detalhes |
|---|---|---|
| Infraestrutura Base de IA | ✅ Concluído | Tabelas `ai_runs` e `prompt_versions` isoladas no Governance DB. |
| Engine de Categorização Automática | 🚀 Planejado Cedo | Conectar um LLM (ex: Gemini) no Promotion Pipeline para classificar dados no Staging. |
| Copilot / Assistente Conversacional | ⏳ Adiado | Chatbot que permite tirar dúvidas ("Onde gastei mais mês passado?"). |

---

## 💻 4. Frontend & UI
Construção visual para que as funcionalidades geradas alcancem o usuário.

| Item | Prioridade / Status | Detalhes |
|---|---|---|
| Estabilização e Tipagem do MVP React | ✅ Concluído | Frontend alinhado, *Zero Any*, rodando liso. |
| UI do Promotion Pipeline Avançado | 🚀 Valor Imediato | Tela de Inbox para promover dados da Staging para Produção com clique duplo. |
| Integração da Nova API | 🚀 Planejado Cedo | React / Next.js consumindo estritamente os contratos recém-validados. |
| UI de Metas e Insights | ⏳ Adiado | Condicionado à criação dos serviços no Backend. |

---

## ⚙️ 5. Operação & Distribuição
Garantia de que a plataforma sobrevive no mundo real.

| Item | Prioridade / Status | Detalhes |
|---|---|---|
| Docker & Compose | ⏳ Adiado | Conteinerização para deploy reprodutível. |
| CI/CD Pipeline Automático | ⏳ Adiado | Bloqueio de PR se Coverage < 70%. |
| Integração Contínua Market Data | ⏳ Adiado | Atualização assíncrona diária de preços (YFinance). |

---

*Última atualização: Junho de 2026 (Transição para Fase de Produto)*
