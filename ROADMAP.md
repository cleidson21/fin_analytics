# fin_analytics_v2 — Roadmap

> Documento vivo. Atualizar status conforme progresso.
> Legenda: ✅ Concluído · 🔄 Em andamento · ⬜ A fazer · 🆕 Adicionado · 🔮 Futuro/Backlog

---

## Status geral

| Módulo | Status |
|---|---|
| Controle Financeiro | ✅ Funcional |
| Módulo Wealth | ✅ Funcional (polish em andamento) |
| Importação CSV | ⬜ Próximo |
| Administração do banco | ⬜ Próximo |
| Governança dos dados | ⬜ Próximo |
| MVP Stabilization | ⬜ Próximo |
| Backup e Restore | ⬜ Próximo |
| Docker | ⬜ Próximo |
| Metas financeiras | ⬜ Planejado |
| Automação Gemini | ⬜ Planejado |
| Market Data / YFinance | ⬜ Planejado |
| Central de Insights | ⬜ Planejado |
| Segurança e testes | ⬜ Planejado |
| CI/CD e documentação | ⬜ Planejado |

---

## Sequência recomendada

```
1.  Finalizar ajustes Wealth / UI (Fase 0)
2.  Importação definitiva CSV MyProfit
3.  Administração do banco
4.  Governança dos dados
5.  MVP Stabilization
6.  Backup e Restore
7.  Docker
8.  Documentação básica
9.  Metas financeiras
10. Python-GenAI (automação Pierre)
11. Rebalanceamento (lógica local)
12. Market Data / YFinance
13. Radar de oportunidades
14. Central de Insights
15. Testes (unitários + integração + E2E)
16. Auditoria de segurança
17. CI/CD
18. Open Finance
19. IA Conversacional
20. Planejamento FIRE
21. Relatório IRPF
```

Lógica da sequência: fechar o ciclo **Entrada de dados → Qualidade dos dados → Planejamento**
antes de investir em automação e inteligência. Metas dependem da consistência de todos os módulos
anteriores — construir em cima de dados inconsistentes gera retrabalho.

---

## ✅ Concluído

### Controle Financeiro

- ✅ Dashboard principal (visão geral, indicadores)
- ✅ Transações
- ✅ Categorias
- ✅ Parcelamentos
- ✅ Relatórios

### Módulo Wealth

- ✅ Executive Home
- ✅ Patrimônio
- ✅ Alocação
- ✅ Dividendos
- ✅ Evolução

### Polish já aplicado

- ✅ Filtro de período como pill-group contido
- ✅ Paleta semântica no Treemap de alocação (RF=#4ecf98, Ações=#7EB8F7, FIIs=#7F77DD, Exterior=#f5a623)
- ✅ KPI cards com valor numérico real (removido placeholder "Consolidado")
- ✅ Marcos patrimoniais como timeline com progresso para próximo marco

---

## 🔄 Fase 0 — Polish e UX (em andamento)

Fechar antes de avançar para novas funcionalidades.

- 🔄 Unificar topbar do módulo Wealth com pills com dot colorido (igual ao dashboard financeiro)
- 🔄 Corrigir idioma dos subtítulos — remover prefixos em inglês:
  - "Growth Dashboard" → "Evolução absoluta do patrimônio e constância de aportes."
  - "Portfolio Risk Desk" → "Análise de concentração de risco e exposição por classe."
  - "Income Dashboard" → "Acompanhamento de renda passiva e reinvestimento acumulado."
  - "Research Desk" → "Análise comparativa de performance e geração de alpha vs benchmarks."
- 🔄 Sub-labels dos KPI cards com regra: dado comparativo → badge colorido / descritivo sem dado → text muted
- 🔄 Benchmark toggle com cor da linha ativa (Carteira/IBOV/CDI/IPCA) e linhas inativas em opacity 0.35
- 🔄 Card "Insight de Risco" do Executive Home — enriquecer com mini donut + Concentração Top 5

---

## ⬜ Fase 1 — Importação MyProfit

**Objetivo:** permitir carga de dados sem dependência de planilhas externas.

- ⬜ Página definitiva de importação com drag and drop
- ⬜ Pré-validação de colunas antes de processar
- ⬜ Preview dos dados antes de confirmar importação
- ⬜ Relatório pós-importação (registros inseridos / ignorados / com erro)
- ⬜ Histórico de importações com data e arquivo

### Provento.csv

- ⬜ Colunas padrão do MyProfit — sem seleção extra necessária pelo usuário

### tableExport.csv (posições da carteira)

- ⬜ Colunas padrão — sem seleção extra necessária pelo usuário

### Evolucao_Carteira.csv

> ⚠️ **Atenção:** este arquivo exige seleção manual de colunas no MyProfit antes do download.
> O sistema deve exibir a lista abaixo como instrução contextual antes do upload.

Colunas obrigatórias a selecionar no MyProfit (20 colunas):

| Grupo | Colunas |
|---|---|
| Base | Data · % Mensal · % Acumulada · Patrimônio · Compras · Vendas · Op. Finalizadas · Proventos |
| IBOV | IBOV Mensal · IBOV Acumulado |
| CDI | CDI Mensal · CDI Acumulado |
| IPCA | IPCA Mensal · IPCA Acumulado |
| IFIX | IFIX Mensal · IFIX Acumulado |
| S&P 500 | S&P Mensal · S&P Acumulado |
| IDIV | IDIV Mensal · IDIV Acumulado |

- ⬜ Validar presença das 20 colunas antes de processar — rejeitar com mensagem clara se alguma faltar
- ⬜ Instrução inline antes do upload com a tabela acima

---

## ⬜ Fase 2 — Administração do banco

**Objetivo:** permitir correção manual de dados pelo admin sem acessar o banco diretamente.

> Reaproveitar estrutura da aba de transações (implementação oculta existente).

- ⬜ Página Banco → Administração
- ⬜ Reclassificação manual de transações (categoria, tipo, parcelamento)
- ⬜ Reclassificação de investimentos e dividendos (classe de ativo, tipo de provento, ticker)
- ⬜ Mesclar categorias com nomes duplicados ou ligeiramente diferentes
- ⬜ Excluir registros órfãos (transações sem categoria, dividendos sem ativo)
- ⬜ Histórico de alterações (log: quem mudou, o quê, quando)
- ⬜ Auditoria simples com campo `audit_log` nas tabelas afetadas

---

## ⬜ Fase 3 — Governança dos dados 🆕

**Objetivo:** criar a camada de confiança do sistema. Dados confiáveis são pré-requisito para Metas e IA.

Fluxo esperado após esta fase:

```
CSV → IA → Banco → Governança → Dashboard → Metas
```

- ⬜ Regras de validação de entrada por tipo de lançamento (PIX, cartão, TED, boleto)
- ⬜ Detecção de duplicatas na importação (mesmo valor + data + descrição)
- ⬜ Score de qualidade dos dados por mês (% de transações sem categoria, sem valor, etc.)
- ⬜ Painel de saúde dos dados — alertas visuais para inconsistências detectadas
- ⬜ Dataset de correções do usuário para uso como few-shots na IA:
  - Cada correção manual salva um exemplo (entrada original → categoria correta)
  - Após N correções, gerar arquivo de few-shots automaticamente
  - Usar nas próximas classificações para melhorar precisão sem re-treinar modelo

---

## ⬜ Fase 4 — MVP Stabilization 🆕

**Objetivo:** estabilizar a base antes de espalhar dependências com o módulo Metas.
Feito aqui, não precisa refazer depois de cada nova funcionalidade.

- ⬜ Resolver todos os warnings do React (chaves únicas, deps de useEffect, etc.)
- ⬜ Revisar e eliminar hooks duplicados entre módulos
- ⬜ Revisar componentes duplicados (Wealth vs Dashboard)
- ⬜ Eliminar tipagens `any` remanescentes — substituir por tipos concretos
- ⬜ Remover `console.log` esquecidos
- ⬜ Resolver todos os `TODO` e `FIXME` documentados no código
- ⬜ Remover imports mortos
- ⬜ Revisar queries lentas — adicionar índices onde necessário
- ⬜ Revisar cache — evitar re-fetch desnecessário ao trocar de aba
- ⬜ Revisar estados globais — garantir consistência entre módulos
- ⬜ Review de performance dos gráficos — avaliar memoização e downsampling de séries longas

---

## ⬜ Fase 5 — Backup e Restore

**Objetivo:** garantir que nenhum dado seja perdido antes de qualquer deploy ou migração.

> Subir de prioridade: colocar antes de Docker. Quando o sistema tiver patrimônio, dividendos,
> metas e histórico real, não pode haver risco de perda.

- ⬜ Exportar banco completo em JSON
- ⬜ Exportar banco em SQLite
- ⬜ Importar backup de volta (restore completo)
- ⬜ Backup incremental (só o que mudou desde o último backup)
- ⬜ Verificação de integridade pós-restore

---

## ⬜ Fase 6 — Docker e documentação

- ⬜ Dockerfile frontend (Next.js, multi-stage build)
- ⬜ Dockerfile backend
- ⬜ `docker-compose.yml` completo (frontend + backend + banco + volumes persistentes)
- ⬜ `.env.example` documentado com todas as variáveis necessárias
- ⬜ README com setup em 3 passos: clone → `docker-compose up` → abrir localhost
- ⬜ Documentação de arquitetura (fluxo de dados, estrutura de pastas, decisões técnicas)
- ⬜ Documentação do módulo Wealth (endpoints, shapes de response, cálculo de alpha e DY)
- ⬜ Documentação dos importadores (colunas por CSV, configuração do pipeline Gemini)
- ⬜ CI/CD com GitHub Actions: lint → testes → build (bloquear merge se falhar)

---

## ⬜ Fase 7 — Metas financeiras

**Objetivo:** fechar o ciclo — transformar o sistema de painel de consulta em ferramenta de decisão.

> Depende de: Importação estável + Governança dos dados + MVP Stabilization.

- ⬜ Estrutura de dados: tabela `goals` (tipo, valor_alvo, prazo, status, progresso)
  - Tipos: `reserva_emergencia`, `viagem`, `imovel`, `independencia_financeira`, `livre`
- ⬜ Integração com Controle Financeiro — saldo mensal médio e sobra média para prazo realista
- ⬜ Integração com Wealth — patrimônio, rentabilidade e dividendos como contribuição às metas
- ⬜ Simulador de cenários: conservador (saldo atual) vs otimista (aumento de aportes/rentabilidade)
- 🆕 Simulador de aportes: "Se eu aportar R$X/mês, quando chego a R$Y?" — usar rentabilidade histórica real
- 🆕 Recomendação de onde aportar: baseado no score de diversificação atual, sugerir classe para próximo aporte (pré-YFinance: lógica local)

---

## ⬜ Fase 8 — Automação com Gemini API

**Objetivo:** eliminar o processo manual de Pierre → cópia → Gemini → ajuste → importação.

- ⬜ Integração `python-genai` (googleapis/python-genai)
- ⬜ Pipeline: mensagem Pierre → Gemini → JSON estruturado → importação automática
- ⬜ Classificação automática: PIX, cartão, TED, boleto → categoria sugerida + grau de confiança
- 🆕 Biblioteca de prompts versionados:
  - `prompt_pix_v1`, `prompt_cartao_v1`, `prompt_fatura_v1`, `prompt_extrato_v1`
  - Versionar para A/B testar qualidade de classificação
- 🆕 Aplicar técnicas de prompt engineering (few-shot, chain-of-thought, output JSON estruturado)
  - Referência: https://www.promptingguide.ai/pt
- 🆕 Alimentar few-shots automaticamente com o dataset de correções da Fase 3 (Governança)

---

## ⬜ Fase 9 — Market Data / YFinance 🆕

**Objetivo:** abstrair o provider de dados de mercado para evitar reescrita futura ao trocar de fonte.

> Implementar camada de abstração antes de usar YFinance diretamente.

Arquitetura:

```
App
 └─ MarketDataService (adapter)
     ├─ YFinance       ← implementar primeiro
     ├─ BrAPI          ← fallback para ativos BR
     ├─ AlphaVantage   ← futuro
     └─ Polygon        ← futuro
```

- ⬜ Criar `MarketDataService` com interface padronizada (preço, DY, valuation)
- ⬜ Implementar adapter YFinance
- ⬜ Recomendações de rebalanceamento (detectar excesso por classe: ações, FIIs, caixa)
- ⬜ Radar de oportunidades: ações com DY alto, FIIs descontados, ativos abaixo do preço médio
- 🆕 Alertas de oportunidade (Telegram ou e-mail) quando ativo atingir condição definida pelo usuário

---

## ⬜ Fase 10 — Central de Insights 🆕

**Objetivo:** superfície unificada que aproveita tudo já construído e entrega inteligência sem esforço do usuário.

Exemplos de insights automáticos:

```
• Seu patrimônio cresceu 4,2% no mês
• Dividendos aumentaram 17% vs ano anterior
• Sua exposição a FIIs caiu abaixo da meta de alocação
• Você gastou 32% mais com alimentação este mês
• Você está 5 meses adiantado na Meta FIRE
• 3 ativos da carteira estão abaixo do preço médio de compra
```

- ⬜ Engine de insights: regras configuráveis por módulo (Controle Financeiro, Wealth, Metas)
- ⬜ Página Central de Insights com feed cronológico
- ⬜ Insights fixados (marcados como importantes pelo usuário)
- ⬜ Notificações internas para insights de alta relevância

---

## ⬜ Fase 11 — Segurança e testes

**Objetivo:** preparar para uso contínuo e eventual exposição além do localhost.

- ⬜ Auditoria de segurança do código gerado por IA:
  - SQL Injection em todas as queries dinâmicas
  - XSS em inputs e renderização de dados externos
  - SSRF em integrações com APIs externas
  - Revisão de autenticação e autorização em todos os endpoints
- ⬜ Eliminar duplicações remanescentes pós-Stabilization
- ⬜ Testes unitários: hooks e utilitários (Jest ou Vitest)
- ⬜ Testes de integração: APIs principais (happy path + cenários de erro)
- ⬜ Testes E2E com Playwright: fluxos críticos (importação, classificação, visualização de patrimônio)

---

## ⬜ Fase 12 — MVP profissional

- ⬜ Aba Configurações: tema, moeda, parâmetros de importação
- ⬜ Aba Perfil: nome, patrimônio alvo, perfil de investidor (base para personalização de metas)

---

## 🔮 Backlog futuro

Sem prazo definido. Entram no roadmap quando houver demanda real.

| Item | Observação |
|---|---|
| Open Finance (Pluggy / Belvo / Quanto) | Substituiria importação manual de extratos |
| Conciliação bancária automática | Depende de Open Finance |
| App Mobile / PWA offline | |
| Multiusuário e compartilhamento familiar | |
| IA conversacional financeira | Chat com contexto da carteira e histórico |
| Integração B3 / CEI automática | |
| Score financeiro próprio | |
| Planejamento FIRE + simulador de aposentadoria | |
| Relatório IRPF automatizado | |
| Alertas por Telegram / WhatsApp | Versão simples pode vir antes (Fase 9) |
| Machine Learning de classificação | Após dataset de correções ser grande o suficiente |

---

## Dependências entre fases

```
Fase 0 (Polish)
    └─ Fase 1 (Importação)
        └─ Fase 2 (Administração)
            └─ Fase 3 (Governança)
                └─ Fase 4 (Stabilization)
                    ├─ Fase 5 (Backup)
                    │   └─ Fase 6 (Docker)
                    └─ Fase 7 (Metas)
                        └─ Fase 8 (Gemini)
                            └─ Fase 9 (Market Data)
                                └─ Fase 10 (Central de Insights)
                                    └─ Fase 11 (Segurança e Testes)
                                        └─ Fase 12 (MVP)
```

---

*Última atualização: junho de 2026*
