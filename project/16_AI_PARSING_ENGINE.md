# 5.4 AI Parser

## Objetivo
Utilizar IA Generativa (OpenAI SDK) para extrair dados estruturados de fontes ruidosas.

## Quando usar
Não será usado em todos os documentos. O uso de tokens deve ser eficiente.
Somente quando:
- Regex falhou ou não existe.
- O resultado do OCR foi de baixa qualidade.
- Arquivos de layout visual extremo (TXT do Pierre).
- Descrição bancária enigmática ou desconhecida.
- Documento de layout inédito.

## Prompting (Fluxo)
Documento (Raw Text) -> LLM -> JSON Canônico

## Regras
Nunca escrever um parser gigante baseado em `if/else` complexo para tentar contornar PDFs frágeis. O LLM cuida da fragilidade do layout e converte em JSON estruturado.
