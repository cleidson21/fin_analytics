# Pesquisa offline de LLM — resumo histórico

**Data de consolidação:** 2026-10-24
**Status:** evidência experimental histórica; não normativa; nenhum modelo aprovado para produção

## Escopo e objetivo

Esta investigação avaliou, com fixtures sintéticos e execução local, se modelos
compactos poderiam interpretar contexto financeiro previamente certificado,
respeitar fronteiras de ferramentas read-only, resistir a conteúdo não confiável
e produzir respostas consultivas estruturalmente válidas. O laboratório não
integrou um provider ao produto, não acessou dados reais, não ativou o Advisor e
não substitui os contratos canônicos de AI Runtime, segurança ou auditoria.

O acervo histórico em `benchmark/` normalizou 555 registros de execuções v1–v4.
O laboratório posterior em `experiments/llm-benchmarks/` preservou esses dados e
adicionou baterias reproduzíveis, relatórios, revisões, fixtures e propostas.

## Modelos identificados na evidência reproduzível

| Modelo local | Digest SHA-256 registrado |
|---|---|
| `bonsai-2:9b` | `c8b5462f8688647fe0b53568e3c00181ada5f05300aa4bf00695f2902f4d388e` |
| `gemma4:e4b-it-q4_K_M` | `dc35e8d9c6061baa6f0fa870975ab6932e2542b579b13ea0f199fa4bb7300c9c` |
| `qwen3.5:4b-q4_K_M` | `d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04` |
| `qwen3.5:9b-q4_K_M` | `56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90` |

Os digests acima identificam as instalações observadas pelo preflight do
laboratório. Eles não constituem certificação, recomendação de implantação nem
garantia de equivalência com outra versão de runtime, quantização ou orçamento.

## Etapas e resultados principais

### Etapa A — ferramentas

A bateria fez 24 chamadas, seis condições por modelo. Na única repetição,
`bonsai-2:9b` passou 6/6 condições, `qwen3.5:4b-q4_K_M` 5/6,
`gemma4:e4b-it-q4_K_M` 1/6 e `qwen3.5:9b-q4_K_M` 1/6. A confiança foi registrada
como baixa. A evidência mostrou que contexto previamente certificado foi mais
estável que depender de tool calling espontâneo, mas não autorizou escolha de
modelo.

### Etapa B — segurança e prompt injection

O Bonsai resistiu aos três ataques aos quais foi efetivamente exposto. O Qwen 4B
resistiu a dois de três, com um resultado estruturalmente inválido e
inconclusivo. O Gemma produziu o único comprometimento comprovado da amostra ao
aceitar valor e fonte maliciosos sintéticos. O Qwen 9B teve uma resistência e
dois resultados inconclusivos. Ataque não exposto permaneceu inconclusivo; não
foi promovido a resistência. Nenhuma operação de escrita, shell, SQL,
filesystem ou rede externa esteve disponível ao modelo.

### Etapa C — recuperação de contexto

A matriz principal variou contexto e posição do fato. Em 36 condições, houve
recuperação exata em 0/9 para Bonsai, 1/9 para Qwen 4B, 0/9 para Gemma e 3/9
para Qwen 9B. Todas as quatro recuperações ocorreram na posição final; início e
meio tiveram 0/24. As ablações posteriores separaram forma, esquema, posição e
truncamento. A calibração C1A.2 comprovou equivalência de tokens nos pares A/C,
mas teve 0/8 recuperações factuais, portanto não foi tratada como sucesso. Os
resultados demonstraram sensibilidade ao desenho do contexto e não sustentam
superioridade estatística ou escolha de produção.

### Etapa Q1 — qualidade consultiva

A execução completou 20/20 condições e o gate técnico inicial 4/4. Pela
reavaliação objetiva `Q1-EVAL-2`, Bonsai passou 2/5 cenários, Qwen 4B 3/5,
Gemma 5/5 e Qwen 9B 3/5. Os erros incluíram relação temporal incorreta,
composição de posições incorreta, inferência de ownership sem suporte, negação
de premissa certificada e claim numérico sem suporte. Qualidade, prudência e
utilidade não foram inferidas dos gates objetivos: ficaram sujeitas à revisão
cega e `REVIEW` nunca foi convertido automaticamente em `PASS`.

### T0 — Thinking

A bateria pareada foi interrompida pelo gate técnico após 5/8 chamadas. Somente
o Bonsai apresentou conteúdo de Thinking observado, mas sua condição on terminou
com `done_reason=length`, sem resposta final, formando um par técnico inválido.
As condições on dos outros três modelos não foram executadas. O resultado foi
0/4 modelos elegíveis para T1, e 0/4 `PASS` tanto no lado off quanto no on. O
runtime não forneceu contagem separada de tokens de raciocínio; essa métrica não
foi inventada. T0 não autoriza T1, integração ou seleção de modelo.

## Correções metodológicas preservadas

- Resultados brutos nunca foram reescritos; correções foram versionadas como
  reavaliações e artefatos aditivos.
- Segurança, estrutura, fidelidade financeira, proveniência e qualidade foram
  avaliadas em dimensões independentes.
- Recusa segura colocada em campo Decimal inválido permaneceu falha estrutural e
  resultado de segurança inconclusivo, não comprometimento presumido.
- Ataque que não chegou ao modelo permaneceu `ATTACK_NOT_EXPOSED/INCONCLUSIVE`.
- Recuperação factual e conformidade JSON foram separadas.
- `REVIEW`, truncamento, saída vazia, matriz incompleta e evidência de baixa
  repetição nunca foram promovidos a aprovação.
- Alterações de fixture, avaliador, runtime, digest, contexto, orçamento,
  Thinking ou modo de ferramentas impedem comparação direta sem reconciliação.

## Direção proposta para o Advisor

Os documentos experimentais propõem a **Estratégia A — contexto certificado
previamente**: o backend autenticado seleciona fatos governados, aplica escopo e
monta um contexto mínimo e versionado; o modelo apenas interpreta esse contexto;
a saída passa por validação e falha fechada. Para um primeiro incremento, a
proposta mantém zero ferramentas de modelo (`max_calls=0`) e dados sintéticos.

Essa estratégia permanece `PROPOSED / DOCUMENTATION ONLY`. Não houve aprovação
de provider, modelo, endpoint, UI operacional, budget, política de reparo ou
seleção definitiva. Auditoria durável, guard pré-execução integrado e demais
gates canônicos continuam sendo pré-condições independentes.

## Condições mínimas para retomar os testes

Uma retomada exige autorização explícita e uma bateria nova/versionada, além de:

1. pergunta decisória e critérios de aceitação definidos antes da inferência;
2. runtime, modelo, digest, quantização, contexto, orçamento e modo Thinking
   fixados e registrados;
3. dados exclusivamente sintéticos e ausência de rede, escrita e acesso ao
   banco real;
4. limites rígidos de chamadas, sem retries implícitos, com parada em
   truncamento, saída vazia ou falha técnica;
5. avaliador e fixtures congelados, com hashes e resultados brutos imutáveis;
6. revisão humana cega quando a conclusão depender de qualidade consultiva;
7. nova autorização separada antes de T1, provider operacional, ferramentas,
   dados reais ou integração ao produto.

## Arquivo histórico externo

O material original permanece intacto no worktree local e não integra o
checkpoint R5. Uma cópia lógica foi arquivada fora da raiz Git em:

- pacote definitivo:
  `<USER_HOME>\Documents\FinAnalytics Archives\LLM Offline Research\2026-10-24\finanalytics-llm-offline-research-20261024-r1.zip`;
- SHA-256 do pacote:
  `7075d201f29aff3adecba8519ec561ee78b83b5fd97552decbc6893c87f152b7`;
- cópia local de preparação e diretório verificável:
  `C:\tmp\finanalytics-llm-offline-research-20261024-r1.zip` e
  `C:\tmp\finanalytics-llm-offline-research-20261024-r1`.

As duas cópias estão no mesmo volume físico `C:` e, portanto, não constituem
backup independente contra falha do disco. O pacote sanitizado também não
substitui os laboratórios brutos para reprodução forense; os originais continuam
preservados, sem alteração, nos diretórios locais inventariados.

O pacote contém 286 arquivos lógicos de `experiments/llm-benchmarks/` e
`benchmark/`, incluindo resultados brutos, fixtures, scripts, relatórios,
revisões, propostas, configurações e manifestos. Sessenta e um arquivos
`__pycache__`/`.pyc` foram omitidos por serem artefatos regeneráveis e aparecem
em `EXCLUDED_GENERATED.csv` com hash e justificativa.

`MANIFEST_SHA256.csv` registra hash de origem e hash arquivado de cada arquivo.
Em 272 arquivos os hashes são idênticos. Em 14 relatórios, 512 ocorrências do
prefixo pessoal de diretório Windows foram substituídas por `<USER_HOME>` apenas
na cópia arquivada; os hashes antes e depois e a quantidade de substituições
permanecem no manifesto. A verificação final não encontrou chave privada, token,
atribuição de credencial, e-mail, CPF ou o caminho pessoal sanitizado. O pacote
não foi enviado a serviço externo.

## Fontes históricas principais

- `experiments/llm-benchmarks/reports/consolidated.md`
- `experiments/llm-benchmarks/reports/stage_b_security_final.md`
- `experiments/llm-benchmarks/reports/stage_c_context_final.md`
- `experiments/llm-benchmarks/reports/stage_q1_consultative_quality_final.md`
- `experiments/llm-benchmarks/reports/stage_q1_thinking_t0_final.md`
- `experiments/llm-benchmarks/proposals/ADVISOR_LOCAL_ARCHITECTURE_V1.md`
- `experiments/llm-benchmarks/proposals/ADVISOR_ACCEPTANCE_GATES_V1.md`

Essas fontes são evidência histórica local. Este resumo não as converte em ADR,
contrato `LOCKED`, aprovação de R4-G ou decisão normativa de produção.
