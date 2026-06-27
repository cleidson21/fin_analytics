# 5.3 OCR Pipeline

## Objetivo
Processar documentos visuais (PDFs baseados em imagem) para extração textual pura.

## Bibliotecas Aprovadas
- **PaddleOCR** (Prioridade principal)
- **Tesseract** (Apenas como fallback)
- **camelot-py** / **tabula-py** (Para extração de tabelas em notas de corretagem)

## Fluxo
PDF -> Imagem -> PaddleOCR -> Texto -> LLM

## Regras
O módulo OCR não interpreta finanças. Ele apenas transforma pixels em strings brutas que serão digeridas pela IA ou Regex depois.
