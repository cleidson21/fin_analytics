# Matriz de Compatibilidade do Importador B3 (Etapa 9)

O objetivo desta matriz é desenhar a estratégia de resiliência e resposta a mudanças bruscas no layout oficial disponibilizado pela B3 no futuro.

## Respostas Comportamentais Esperadas do Reader/Parser

| Evento / Modificação no Arquivo Físico | Impacto Estimado | Comportamento Exigido do Parser/Reader |
| :--- | :--- | :--- |
| **A Ordem das Colunas mudar** | Baixo | O `pandas` no Reader extrairá os dados mapeando via `Nome do Cabeçalho` (keys explícitas) e não por `Index` (índice da coluna). A ordem não importa. |
| **Aparecer uma Coluna Nova (Desconhecida)**| Muito Baixo | O Parser deve usar um filtro de chaves de extração (`subset`). Colunas desconhecidas serão completamente ignoradas (`df = df[colunas_alvo]`). |
| **Removerem uma Coluna Opcional** | Baixo/Médio | Exemplo: "Mercado". Se desaparecer, o Parser interceptará o `KeyError` inicial e atribuirá um valor default (nulo) dinamicamente sem quebrar a pipeline inteira. |
| **Removerem uma Coluna Obrigatória** | Crítico (Fatal) | Exemplo: "Quantidade". O Parser lançará uma falha formal de layout (`LayoutMismatchError`) avisando o usuário que o arquivo da B3 não é mais o esperado. O processo aborta por segurança. |
| **Surgir nova Aba (Sheet)** | Muito Baixo | O Reader procurará nominalmente pela aba `Negociação`. Se não achar, procura a alternativa canônica `Movimentação`. Outras abas serão ignoradas pela engine (o `sheet_name` estará travado). |
| **O Arquivo vier com uma Aba Vazia** | Médio | O `len(df)` retornará zero após o Parser processá-lo e dropar eventuais cabeçalhos flutuantes. O pipeline se encerrará prematuramente com Warning de "Sucesso, porém sem dados injetados". |
| **Planilhas Ocultas no Excel** | Nenhum | A engine `openpyxl` acessa as planilhas pelo XML interno. Ela ignora a flag de visualização "hidden" nativa do MS Excel se chamada nominalmente, extraindo os dados independentemente do estado visual. |

## Diretriz de Evolução (Contract Tests)

Para garantir que a resposta teórica seja funcional na prática, a **Sprint de Testes** (no futuro) deverá ser obrigada a injetar planilhas corrompidas e mockar essas variações de colunas via pytest para avaliar se a pipeline morre agressivamente (Fail-Fast seguro) ou perdoa de forma resiliente, como documentado acima.
