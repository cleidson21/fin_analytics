
# VISÃO DO PRODUTO — WEALTH INTELIGENCE

> **Papel deste documento:** `HIGH-LEVEL PRODUCT VISION`. Os contratos executáveis de microfase e o estado canônico ficam em `project/wealth-intelligence/`.

## O que a aba deve ser ao final do Lote 10

**Status atual:** Goals 10.1 e Financial Health 10.2 concluídos; Planning 10.3 ainda não iniciado.
**Baseline:** FINANALYTICS V3.1.0 — Investments estabilizado
**Objetivo:** Transformar a área de patrimônio em um **centro inteligente de planejamento, acompanhamento e orientação financeira pessoal**, conectando patrimônio, metas, aposentadoria, carteira, mercado, oportunidades e inteligência artificial.

> **Regra principal:** o Wealth Intelligence não deve ser apenas um CRUD de metas. Deve funcionar como um **Wealth OS pessoal**, capaz de entender a situação financeira do usuário, acompanhar objetivos, projetar cenários, identificar oportunidades e riscos e utilizar IA para interpretar essas informações.

---

# 1. VISÃO DO PRODUTO FINAL

Ao final do Lote 10, o usuário deverá conseguir entrar em uma única área e responder:

* Quanto tenho hoje?
* Como está minha saúde financeira?
* Estou evoluindo ou regredindo?
* Minhas metas estão no caminho certo?
* Quanto preciso investir por mês?
* Quando poderei atingir determinado objetivo?
* Quando poderei atingir independência financeira?
* Como será minha aposentadoria?
* Minha carteira está adequada aos meus objetivos?
* Quais ativos estão contribuindo mais ou menos para meu patrimônio?
* O que aconteceu recentemente com minha carteira?
* Algum ativo caiu significativamente?
* Existe alguma oportunidade que atende aos critérios que defini?
* Há notícias relevantes sobre meus ativos?
* O mercado está mudando de alguma forma que merece minha atenção?
* O que o sistema recomenda que eu acompanhe?
* O que o Ollama/LLM consegue interpretar sobre minha situação?

---

# 2. ESTRUTURA FUNCIONAL DA ABA

A área deverá evoluir para aproximadamente os seguintes módulos:

### 🏠 Dashboard / Visão Geral

Painel principal com:

* patrimônio atual;
* patrimônio líquido;
* evolução patrimonial;
* rentabilidade;
* aportes;
* proventos;
* situação das metas;
* saúde financeira;
* progresso para independência financeira;
* principais acontecimentos;
* alertas;
* oportunidades;
* briefing inteligente.

---

# 3. METAS

As metas serão o núcleo de planejamento do Wealth Intelligence.

O usuário deverá poder criar, visualizar, editar, pausar, concluir ou cancelar objetivos.

Exemplos:

* Reserva de emergência;
* Compra de imóvel;
* Compra de veículo;
* Viagem;
* Patrimônio-alvo;
* Investimento específico;
* Renda de dividendos;
* Independência financeira;
* Aposentadoria;
* Meta personalizada.

Cada meta deverá possuir, conforme aplicável:

* nome;
* tipo;
* valor-alvo;
* valor atual;
* prazo;
* prioridade;
* aporte mensal planejado;
* conta/ativo relacionado;
* premissas;
* progresso;
* projeção;
* status.

### Evolução esperada

**10.1 — Fundação das metas**
→ cadastro, edição, exclusão, progresso básico.

**10.3 — Inteligência das metas**
→ cálculos, projeções, cenários e aporte necessário.

---

# 4. PLANEJAMENTO FINANCEIRO

O sistema deverá deixar de apenas mostrar o patrimônio e passar a responder:

> **“O que preciso fazer para chegar onde quero?”**

Deverá permitir:

* calcular aporte mensal necessário;
* calcular prazo estimado;
* calcular patrimônio futuro;
* comparar diferentes níveis de aporte;
* simular rentabilidades;
* considerar inflação;
* comparar cenários conservador/base/otimista;
* visualizar impacto de aumentar ou reduzir aportes;
* identificar metas atrasadas ou adiantadas.

---

# 5. APOSENTADORIA

Deverá existir um módulo específico de planejamento de aposentadoria.

O usuário poderá informar:

* idade atual;
* idade desejada para aposentadoria;
* patrimônio atual;
* renda mensal desejada;
* gastos mensais;
* aportes;
* rentabilidade esperada;
* inflação;
* outros parâmetros relevantes.

O sistema deverá projetar:

* patrimônio futuro;
* renda potencial;
* patrimônio necessário;
* aporte necessário;
* idade estimada para atingir o objetivo;
* diferentes cenários;
* distância até a independência financeira.

---

# 6. INDEPENDÊNCIA FINANCEIRA / FIRE

O Wealth Intelligence deverá possuir uma visão específica de independência financeira.

Deverá relacionar:

**Patrimônio + despesas + aportes + rentabilidade + renda passiva + tempo.**

O sistema deverá mostrar:

* patrimônio atual;
* patrimônio necessário;
* percentual alcançado;
* renda passiva atual;
* renda desejada;
* distância até a independência;
* estimativa de quando poderá atingir o objetivo;
* evolução histórica;
* cenários.

A ideia não é apenas mostrar uma calculadora FIRE, mas acompanhar a **trajetória financeira do usuário**.

---

# 7. SAÚDE FINANCEIRA

O sistema deverá analisar a vida financeira como um todo.

Indicadores esperados:

* receitas;
* despesas;
* taxa de poupança;
* capacidade de aporte;
* evolução dos gastos;
* concentração de despesas;
* tendências por categoria;
* anomalias;
* estabilidade financeira;
* capacidade de investimento.

Deverá responder perguntas como:

> “Estou gastando mais que nos meses anteriores?”

> “Minha capacidade de aporte está aumentando?”

> “Qual categoria está pressionando meu orçamento?”

> “Minha taxa de poupança está melhorando?”

---

# 8. INTELIGÊNCIA DA CARTEIRA

A área deverá analisar o patrimônio investido sem substituir a área Investments existente.

Deverá identificar:

* maiores posições;
* melhores e piores desempenhos;
* contribuição de cada ativo para o patrimônio;
* contribuição para rentabilidade;
* concentração;
* exposição por classe;
* evolução dos investimentos;
* dividendos;
* comportamento histórico.

Também deverá responder:

> “O que está fazendo meu patrimônio subir?”

e

> “O que está prejudicando minha carteira?”

---

# 9. RADAR DE QUEDAS E EVENTOS

O sistema deverá identificar acontecimentos relevantes.

Exemplos:

* queda expressiva de um ativo;
* alta expressiva;
* mudança relevante de preço;
* alteração de fundamentos;
* notícia importante;
* divulgação de resultados;
* eventos corporativos;
* mudanças macroeconômicas.

Quando possível, deverá buscar informações externas para explicar o movimento.

**Importante:** o sistema não deverá inventar uma explicação.

Deverá trabalhar com:

**evento → dados → fonte → interpretação.**

---

# 10. OPORTUNIDADES

O Wealth Intelligence deverá possuir uma área de oportunidades/watchlist.

O usuário poderá acompanhar ativos ou oportunidades que deseja monitorar.

Exemplos de critérios:

* preço;
* queda percentual;
* valuation;
* dividend yield;
* indicadores fundamentalistas;
* indicadores técnicos;
* notícias;
* determinados eventos;
* preço-alvo definido pelo usuário;
* condições personalizadas.

O sistema deverá identificar quando uma condição previamente definida for atingida.

### Exemplo

> “Avisar quando determinado ativo cair 10%.”

ou

> “Avisar quando o DY atingir determinado nível.”

ou

> “Monitorar ativos que atendam aos meus critérios de valuation.”

---

# 11. WATCHLIST

Deverá existir uma lista de ativos acompanhados pelo usuário.

Cada ativo poderá possuir:

* preço atual;
* variação;
* histórico;
* fundamentos;
* notícias;
* eventos;
* indicadores;
* critérios configurados;
* alertas;
* situação perante os critérios definidos.

A watchlist será uma das fontes do **Radar de Oportunidades**.

---

# 12. INTELIGÊNCIA DE MERCADO

O sistema deverá integrar fontes externas para enriquecer as informações.

Possíveis fontes:

* preços de mercado;
* histórico;
* indicadores;
* BCB;
* notícias;
* dados fundamentalistas;
* CVM/B3;
* provedores externos;
* consenso de mercado quando disponível.

A arquitetura deverá manter claramente a distinção entre:

**dados internos governados**
e
**dados externos/enriquecimento.**

---

# 13. NOTÍCIAS E CONTEXTO

O sistema deverá buscar notícias relevantes para:

* ativos da carteira;
* ativos da watchlist;
* mercado;
* economia;
* indicadores macroeconômicos.

As informações deverão possuir:

* fonte;
* data;
* ativo/assunto relacionado;
* grau de relevância;
* contexto.

A prioridade é apresentar **informação útil**, e não simplesmente uma lista de notícias.

---

# 14. OLLAMA / INTELIGÊNCIA ARTIFICIAL

O Ollama deverá ser utilizado como camada de inteligência local, sempre que possível.

A arquitetura deverá permitir posteriormente outros providers, como:

* Ollama;
* Gemini;
* OpenAI;
* outros providers compatíveis.

### Papel da IA

A IA deverá:

* interpretar dados;
* resumir;
* explicar;
* cruzar informações;
* identificar padrões;
* contextualizar acontecimentos;
* produzir briefing;
* responder perguntas;
* apresentar cenários;
* explicar indicadores;
* auxiliar na tomada de decisão.

### A IA NÃO deverá:

* inventar dados;
* inventar notícias;
* inventar consenso;
* alterar patrimônio;
* alterar transações;
* alterar posições;
* calcular a verdade financeira por conta própria;
* executar operações de compra/venda.

**Princípio:**

> **Backend calcula. Banco governa. IA interpreta.**

---

# 15. WEALTH COPILOT

Em estágio posterior, o usuário deverá poder conversar com seu patrimônio.

Exemplos:

> “Como está minha situação financeira?”

> “Como estão minhas metas?”

> “Estou evoluindo para minha aposentadoria?”

> “O que aconteceu com minha carteira esta semana?”

> “Quais ativos tiveram maior impacto no meu patrimônio?”

> “Existe alguma oportunidade na minha watchlist?”

> “Por que meu patrimônio caiu?”

> “O que preciso fazer para atingir minha meta em 10 anos?”

A resposta deverá ser baseada no **contexto financeiro real do usuário**, fornecido pelo backend.

---

# 16. BRIEFING FINANCEIRO INTELIGENTE

O sistema deverá produzir periodicamente um resumo personalizado.

Exemplo:

### Seu resumo financeiro

**Patrimônio**

* evolução do patrimônio;
* principais variações.

**Carteira**

* maiores altas;
* maiores quedas;
* contribuição dos ativos.

**Metas**

* metas avançando;
* metas atrasadas;
* necessidade de aporte.

**Saúde financeira**

* evolução dos gastos;
* taxa de poupança.

**Mercado**

* eventos relevantes.

**Oportunidades**

* condições atingidas na watchlist.

**Atenção**

* situações que merecem acompanhamento.

---

# 17. ALERTAS

O sistema deverá possuir uma camada de alertas inteligentes.

Exemplos:

* meta atrasada;
* aporte abaixo do planejado;
* queda relevante;
* mudança de patrimônio;
* alteração significativa de gastos;
* oportunidade atingida;
* notícia relevante;
* evento de ativo;
* mudança macroeconômica.

Os alertas deverão ser classificados por relevância/severidade.

---

# 18. SIMULAÇÕES

O usuário deverá poder testar cenários sem alterar seus dados reais.

Exemplos:

> “E se eu investir R$ 1.000 por mês?”

> “E se aumentar para R$ 2.000?”

> “E se a rentabilidade for menor?”

> “E se eu me aposentar aos 50?”

> “E se reduzir meus gastos?”

> “Quanto tempo ganho aumentando meus aportes?”

As simulações devem ser **isoladas**, determinísticas e nunca modificar os dados financeiros reais.

---

# 19. PRINCÍPIO DE INTEGRAÇÃO

O Wealth Intelligence deverá utilizar os dados que já existem no FINANALYTICS.

Fluxo conceitual:

**Transações / Investimentos / Mercado / Despesas / Metas**

↓

**Read Models certificados**

↓

**Serviços determinísticos**

↓

**Contexto financeiro**

↓

**Ollama / LLM**

↓

**Insights / Explicações / Briefings / Cenários**

O LLM nunca deverá ser a fonte primária dos dados financeiros.

---

# 20. EXPERIÊNCIA FINAL ESPERADA

A experiência deverá evoluir de:

> **“Aqui estão meus investimentos.”**

para:

> **“Aqui está minha situação financeira, onde estou, para onde estou indo, o que pode acontecer e quais pontos merecem minha atenção.”**

E posteriormente:

> **“Converse com seu patrimônio e tome decisões melhores com base nos seus próprios dados.”**

---

# 21. ROADMAP PARA CHEGAR AO PRODUTO FINAL

| Fase            | Objetivo                                      | Situação    |
| --------------- | --------------------------------------------- | ------------- |
| **10.0**  | Auditoria, arquitetura e estabilização      | ✅ Concluído |
| **10.1**  | Fundação das Metas                          | 🔜 Próxima   |
| **10.2**  | Saúde Financeira                             | ⏳            |
| **10.3**  | Cálculos, projeções e simulações         | ⏳            |
| **10.4**  | Aposentadoria / FIRE                          | ⏳            |
| **10.5**  | Inteligência da Carteira                     | ⏳            |
| **10.6**  | Alocação, rebalanceamento e Watchlist       | ⏳            |
| **10.7**  | Mercado, notícias e oportunidades            | ⏳            |
| **10.8**  | Ollama / LLM / IA                             | ⏳            |
| **10.9**  | Wealth Copilot / Briefing                     | ⏳            |
| **10.10** | Multi-Agent avançado, somente se justificado | ⏳            |
| **10.11** | Docker / operação / infraestrutura          | ⏳            |
| **10.12** | UX global / acabamento final                  | ⏳            |

---

# 22. ONDE ESTAMOS AGORA

### Já consolidado

✅ Investments V3 estabilizado
✅ Importação e governança MyProfit
✅ Patrimônio e posições
✅ Evolução patrimonial
✅ Proventos
✅ Allocation
✅ Histórico de dividendos
✅ Market Data / yfinance
✅ Asset Detail
✅ APIs de Wealth
✅ Baseline `v3.1.0-investments`
✅ Auditoria arquitetural do Lote 10
✅ Conflito de `position_snapshots` investigado e resolvido
✅ Dependências principais corrigidas
✅ Documentação-base do Wealth Intelligence criada
✅ Decisões arquiteturais principais registradas

### Situação atual

🟡 **Lote 10.0-A concluído — READY FOR 10.1**

A próxima entrega é a **fundação das Metas**.

Ainda **não** estamos na fase de:

* aposentadoria;
* FIRE;
* oportunidades;
* watchlist;
* notícias;
* Ollama;
* Copilot;
* agentes.

Esses componentes dependem das fases seguintes.

---

# 23. COMO SABER SE O PROJETO ESTÁ NO CAMINHO CERTO

A cada nova etapa, a pergunta principal deve ser:

> **“Esta implementação aproxima o sistema do Wealth Intelligence descrito aqui ou está apenas adicionando funcionalidades isoladas?”**

### Sinais de que está no caminho certo

✅ Cada módulo utiliza dados reais e governados.
✅ Cálculos financeiros são determinísticos.
✅ IA interpreta dados, não inventa a verdade.
✅ Metas se conectam posteriormente às finanças reais.
✅ Projeções utilizam premissas explícitas.
✅ Watchlist gera oportunidades baseadas em critérios.
✅ Notícias possuem fonte e data.
✅ Alertas possuem motivo verificável.
✅ O usuário consegue entender de onde cada informação veio.
✅ Os módulos conversam entre si.
✅ A interface evolui sem destruir o `/wealth` existente.
✅ Segurança e isolamento por usuário permanecem obrigatórios.

### 🚨 Sinais de desvio

❌ Criar apenas um CRUD de metas e chamar isso de Wealth Intelligence.
❌ IA calculando patrimônio.
❌ IA inventando notícias ou dados.
❌ Dados externos substituindo dados governados.
❌ Criar módulos isolados que não conversam entre si.
❌ Criar funcionalidades sem fonte de dados definida.
❌ Alterar Investments sem necessidade.
❌ Criar uma segunda arquitetura de mercado/yfinance.
❌ Adicionar LangGraph/CrewAI apenas para dizer que existe “multi-agent”.
❌ Criar telas bonitas sem backend determinístico.
❌ Criar cálculos sem explicar suas premissas.
❌ Mostrar projeções como se fossem certezas.

---

# 24. DEFINIÇÃO DE PRONTO DO WEALTH INTELLIGENCE

O produto poderá ser considerado **funcionalmente completo** quando o usuário conseguir:

**1. Conhecer sua situação financeira**
↓
**2. Definir objetivos**
↓
**3. Saber quanto precisa investir**
↓
**4. Projetar seu futuro**
↓
**5. Planejar aposentadoria/FIRE**
↓
**6. Acompanhar sua carteira**
↓
**7. Monitorar ativos e oportunidades**
↓
**8. Receber contexto de mercado e notícias**
↓
**9. Receber alertas relevantes**
↓
**10. Conversar com uma IA que conhece seus dados financeiros**
↓
**11. Simular decisões sem alterar sua realidade**
↓
**12. Acompanhar continuamente se está mais perto ou mais longe dos seus objetivos.**

---

## PRINCÍPIO FINAL

> **O Wealth Intelligence não deve ser uma coleção de telas financeiras.**
>
> Deve ser uma camada inteligente sobre o FINANALYTICS capaz de transformar **dados → diagnóstico → planejamento → projeção → monitoramento → contexto → inteligência**, mantendo os dados financeiros sob governança determinística e utilizando o LLM como **copiloto**, não como fonte da verdade.

**Progresso geral:** a fundação técnica e os investimentos estão estabilizados; o **Lote 10.0-A está concluído** e o projeto está agora no ponto de iniciar a **fundação das Metas (10.1)**. A partir daí, as fases 10.2–10.9 constroem progressivamente a visão completa acima.
