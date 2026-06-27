# IMPORTERS CATALOG

Catálogo e acompanhamento dos plugins de importação desenvolvidos no FinAnalytics V3.

---

### Nubank (Conta Corrente)
- **Status:** Planejado
- **Formato:** CSV
- **Encoding:** UTF-8
- **Dependências:** `pandas`, `Normalizer (Nubank -> Canonical)`
- **Testes:** Pendente
- **Detalhes:** Arquivo vital (Possui UUID). Raiz de fluxo de caixa.

---

### Nubank (Fatura Cartão)
- **Status:** Planejado
- **Formato:** CSV
- **Encoding:** UTF-8
- **Dependências:** `pandas`, `Normalizer (Credit -> Canonical)`
- **Testes:** Pendente
- **Detalhes:** Não possui UUID. A Reconciliação deverá associar o pagamento na fatura ao débito gigante na Conta Corrente.

---

### B3 (Área do Investidor)
- **Status:** Planejado
- **Formato:** XLSX (Frequentemente baixado como .csv errôneo)
- **Encoding:** Binary / ZIP
- **Dependências:** `openpyxl`, `Normalizer (Position -> Canonical)`
- **Testes:** Pendente
- **Detalhes:** Domina a reconciliação de quantidades de ativos.

---

### Notas de Corretagem (Padrão SINACOR)
- **Status:** Planejado
- **Formato:** PDF
- **Encoding:** PDF / OCR
- **Dependências:** `pdfplumber`, `camelot-py` (Tabelas), `PaddleOCR` (Scans)
- **Testes:** Pendente
- **Detalhes:** Domina preço médio, taxas B3 e emolumentos. Pode necessitar de Fallback IA se o PDF for vetorizado quebrado.

---

### Pierre (Agregador Categoria)
- **Status:** Planejado
- **Formato:** TXT Visual
- **Encoding:** UTF-8
- **Dependências:** Regex, `OpenAI SDK` (AI Parser Fallback)
- **Testes:** Pendente
- **Detalhes:** Formato instável (Emojis e espaços posicionalmente ruidosos). Função: Injetar `category_id` (Teacher Forcing).

---

### MyProfit
- **Status:** Planejado
- **Formato:** CSV
- **Encoding:** UTF-8 / Latin-1
- **Dependências:** `pandas`, `Normalizer (Dividend/Yield -> Canonical)`
- **Testes:** Pendente
- **Detalhes:** Enriquece metadados de proventos (Data COM, YOC, DY) não encontrados na B3.
