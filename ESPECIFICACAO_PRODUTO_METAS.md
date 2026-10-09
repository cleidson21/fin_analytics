# VISÃO PESSOAL DO PRODUTO — FINANALYTICS WEALTH INTELLIGENCE

> **Natureza:** visão resumida do produto final, organizada pela ordem de evolução do projeto. Este documento expressa a experiência desejada; **não** é checklist, cronograma, status de implementação, contrato técnico ou autorização para desenvolver funcionalidades.
>
> **Governança:** `project/wealth-intelligence/MASTER_PLAN.md` permanece como referência canônica da visão; `ARCHITECTURE.md` define o mapa do produto e `IMPLEMENTATION_ROADMAP.md` define a sequência e o estado oficial das fases. Em caso de divergência, prevalecem os documentos e ADRs aprovados.

## O produto que desejo construir

Quero que o FinAnalytics evolua de um sistema que registra transações e acompanha investimentos para um **Wealth OS pessoal**: um lugar onde eu consiga compreender minha situação financeira, estabelecer objetivos, projetar caminhos possíveis, acompanhar o patrimônio, identificar riscos e receber explicações úteis sobre o que está acontecendo.

A experiência final deverá responder, de forma integrada: **onde estou, para onde quero ir, quanto preciso investir, como estou evoluindo e o que merece minha atenção**. Não quero uma coleção de telas independentes, mas um sistema em que os módulos utilizem as mesmas informações confiáveis e se complementem.

## 1. Base financeira e investimentos

A evolução começa com os dados já presentes no FinAnalytics: transações, contas, classificação de receitas e despesas, importações, investimentos, posições, proventos e evolução patrimonial. Quero visualizar o patrimônio investido, seu histórico, minha alocação e os rendimentos, com clareza sobre a origem e as limitações de cada informação.

O patrimônio agregado de investimentos deve respeitar a fonte certificada já definida pelo projeto. Cotações ou posições parciais não podem ser somadas para produzir uma nova verdade patrimonial; patrimônio investido e patrimônio líquido pessoal também não devem ser confundidos.

## 2. Metas e saúde financeira

A partir dessa base, quero **definir e acompanhar metas** como reserva de emergência, imóvel, viagem, patrimônio-alvo, renda de dividendos e independência financeira. Cada objetivo deve mostrar seu progresso, prazo e necessidades de planejamento, sem transformar estimativas em fatos.

Quero também entender **quanto recebo, quanto gasto, quanto consigo poupar e como esses padrões mudam**. A saúde financeira deve destacar tendências, concentração de despesas e anomalias, permitindo relacionar hábitos financeiros aos objetivos. Uma sobra observada não deve ser tratada automaticamente como aporte futuro garantido.

## 3. Planejamento, simulações e independência financeira

Com as metas e a saúde financeira conectadas, quero responder a perguntas como: **quanto preciso investir por mês, em quanto tempo alcançarei um objetivo e como o resultado muda se eu alterar meus aportes?**

Quero comparar cenários de patrimônio futuro, inflação e rentabilidade, incluindo planejamento de aposentadoria e independência financeira (FIRE). Gastos desejados, taxa de retirada, aportes e retornos projetados devem ser premissas explícitas, escolhidas ou confirmadas por mim. As simulações são hipóteses; não devem modificar transações, posições nem valores reais.

## 4. Contexto financeiro pessoal inteligente — R2

O sistema deve reunir, de maneira controlada, **o que declarei, o que foi observado e o que foi calculado**. Quero poder informar dados pessoais financeiros relevantes, revisar possíveis rendas recorrentes identificadas nas transações e confirmar ou rejeitar essas interpretações.

Esse contexto deverá ajudar outras áreas a entender minha realidade, sem preencher automaticamente informações ausentes ou impor uma única regra de precedência para todos os módulos. A ausência de um dado precisa continuar visível como ausência.

## 5. Referências econômicas e de mercado — R3

Quero compreender meus objetivos também à luz do ambiente econômico: **Selic, CDI, IPCA, câmbio e, futuramente, expectativas e informações de mercado**, sempre com fonte, unidade, período, data de obtenção e indicação de atualidade ou indisponibilidade.

Essas informações servem para contextualizar decisões, não para substituir meus dados financeiros nem escolher sozinhas a inflação, o retorno ou qualquer outra premissa de uma simulação. Informações históricas devem poder ser consultadas respeitando o que o sistema efetivamente conhecia em cada momento. Cotações externas e notícias exigem cuidados próprios com qualidade e direito de uso.

## 6. Inteligência artificial como camada consultiva — R4 e evolução posterior

Quero conversar com o FinAnalytics sobre minha situação financeira, metas e carteira, perguntando, por exemplo: **“Por que meu patrimônio mudou?”, “Como estão minhas metas?” ou “Que riscos merecem minha atenção?”**

A IA deverá interpretar informações entregues pelos serviços confiáveis do backend, explicar resultados, resumir tendências e ajudar a comparar cenários. Quero flexibilidade para utilizar **Gemini ou modelos locais via Ollama**, conforme disponibilidade, custo e adequação técnica; outros provedores poderão ser considerados, sem se tornarem obrigatórios.

O princípio é simples: **o backend calcula, os dados governados sustentam a resposta e a IA interpreta**. Ela não deve inventar fatos, notícias, rendimentos ou recomendações com aparência de certeza, alterar registros financeiros nem executar compras ou vendas.

## 7. Experiência integrada e orientação prática — R6 e demais etapas previstas

Quando as foundations estiverem prontas, quero uma experiência unificada: visão geral do patrimônio, saúde financeira, metas, planejamento, FIRE e contexto econômico trabalhando juntos. O sistema poderá **sugerir informações para preenchimento**, mas deverá mostrar sua origem e exigir minha escolha quando forem premissas ou decisões pessoais.

O painel principal deve permitir identificar rapidamente o que mudou, o progresso dos objetivos e os pontos que merecem atenção. As etapas intermediárias e seus limites são os definidos pelo roadmap canônico, sem antecipar funcionalidades de fases ainda não autorizadas.

## 8. Inteligência da carteira — após as foundations previstas

Quero compreender a composição e a evolução dos meus investimentos sem substituir a área Investments já existente. A análise deverá ajudar a visualizar concentração, exposição por classe, renda distribuída, evolução e, **quando houver dados suficientes e certificados**, contribuição dos ativos para resultados e riscos.

A inteligência da carteira só deve apresentar desempenho, causalidade e valuations quando existir base verificável para calculá-los. Se a granularidade necessária não estiver disponível, prefiro que o sistema explique a limitação a receber uma estimativa inventada.

## 9. Monitoramento, watchlist, oportunidades e notícias — expansão futura

Quero acompanhar ativos de interesse e configurar condições pessoais, como mudanças relevantes de preço, metas de dividendos ou outros critérios verificáveis. Com fontes adequadas, o FinAnalytics poderá apresentar **alertas, eventos corporativos, contexto macroeconômico, notícias relevantes e oportunidades que atendam às regras que eu defini**.

Esses recursos devem explicar **qual condição foi atendida, quando, com quais dados e de qual fonte**. Notícias não devem ser usadas para inventar causas de oscilações. Um radar de oportunidades deve apoiar meu julgamento, não funcionar como ordem automática de investimento.

## 10. Copiloto, briefings e acompanhamento contínuo — experiência final

O resultado desejado é um **copiloto financeiro pessoal** capaz de reunir periodicamente os acontecimentos mais importantes: evolução do patrimônio, metas, despesas, rendimentos, carteira, mercado e alertas relevantes. Quero poder aprofundar cada informação, compreender suas premissas e formular novas perguntas.

A experiência final deve permitir perceber se estou **mais perto ou mais longe dos meus objetivos**, o que está contribuindo para isso e quais decisões posso avaliar. Briefings, automações e recursos avançados só deverão existir quando houver dados, fontes, segurança e utilidade comprovada; não são fins em si mesmos.

## Princípios que não quero perder

A evolução precisa preservar **dados confiáveis, cálculos determinísticos, proveniência, privacidade, segurança, transparência de premissas e distinção entre realidade e simulação**. Dados externos enriquecem o contexto; não substituem fatos internos certificados. A IA interpreta; não governa patrimônio. Novas funcionalidades devem aproveitar o sistema existente sem criar arquiteturas paralelas desnecessárias.

> **Minha visão final:** abrir o FinAnalytics e entender minha vida financeira em conjunto — **o que tenho, o que gasto, onde quero chegar, quais caminhos posso seguir e o que vale acompanhar** — com explicações claras, informações rastreáveis e controle sobre minhas próprias decisões.
