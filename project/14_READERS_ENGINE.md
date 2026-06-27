# 5.2 Readers

## Objetivo
Realizar a leitura bruta de arquivos utilizando apenas bibliotecas dedicadas, sem nenhuma lógica financeira.

## Bibliotecas Aprovadas
- **CSV**: `pandas`
- **XLSX**: `openpyxl`
- **PDF**: `pdfplumber`, `PyMuPDF`
- **TXT**: Parser Base / Regex / Fallback LLM

## Regras e Fluxo (RawDocument)
Todos os Readers processam a I/O bruta e devem obrigatoriamente devolver uma estrutura purificada chamada `RawDocument` que servirá de input para o Normalizer. Nunca gravam no banco, classificam, ou conciliam.

Exemplo abstrato do output de um Reader:
```json
{
  "source": "NUBANK_ACCOUNT_CSV",
  "filename": "extrato_2026.csv",
  "mime": "text/csv",
  "encoding": "utf-8",
  "rows": [{"data": "...", "valor": "...", "desc": "..."}],
  "metadata": {"user": "cleidson"},
  "hash": "b2f5a...",
  "created_at": "2026-06-25T10:00:00",
  "parser_version": "1.0.0"
}
```
Isso isola o parsing físico (bytes para dicts) do parsing semântico (dicts para Canonical Events).
