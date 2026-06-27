# 5.9 Learning Engine

## Objetivo
Criar um módulo próprio para ensinar o classificador financeiro interno usando dados empíricos, de modo a descontinuar agregadores de terceiros.

## Fluxo (Teacher Forcing via Pierre)
1. Extrato **Pierre** (App Terceiro).
2. Extração da **Categoria** validada por humanos.
3. Geração de **Training Example** usando as features do extrato bancário (ex: "Transf. Pix Maria").
4. Vetorização via **Embeddings** (OpenAI).
5. Armazenamento local usando **FAISS** (Rápido, testado e eficiente).
6. Execução iterativa via **Classificador**.

## Resultado Esperado
Após milhares de exemplos consolidados no banco de vetores FAISS, o aplicativo de terceiros (Pierre) pode ser descartado permanentemente. O Classificador do FinAnalytics assumirá sozinho a dedução de categorias com altíssima confiança.
