# IMPORTERS CATALOG

Catálogo e acompanhamento dos plugins de importação desenvolvidos no FinAnalytics V3.

---

### Nubank (Conta Corrente)
- **Status:** Implementado
- **Formato:** CSV
- **Encoding:** UTF-8
- **Dependências:** `pandas`, `Normalizer (Nubank -> Canonical)`
- **Testes:** Concluído
- **Detalhes:** Arquivo vital (Possui UUID). Raiz de fluxo de caixa.

---

### Nubank (Fatura Cartão)
- **Status:** Implementado
- **Formato:** CSV
- **Encoding:** UTF-8
- **Dependências:** `pandas`, `Normalizer (Credit -> Canonical)`
- **Testes:** Concluído
- **Detalhes:** Não possui UUID. A Reconciliação deverá associar o pagamento na fatura ao débito gigante na Conta Corrente.

---

---

### MyProfit (Proventos)
- **Status:** Implementado (TSK-5.5-1)
- **Formato:** CSV
- **Encoding:** UTF-8 / Latin-1
- **Dependências:** `pandas`, `Normalizer (Dividend/Yield -> Canonical)`
- **Testes:** Concluído (80 testes unitários, testes funcionais OK)
- **Detalhes:** Enriquece metadados de proventos (Data COM, YOC, DY). Arquivo de Ativos descartado por incompatibilidade de formato transacional. Mapeado como EA4-NEW-001.

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
- **Status:** Implementado
- **Formato:** TXT Visual
- **Encoding:** UTF-8
- **Dependências:** Regex, `OpenAI SDK` (AI Parser Fallback)
- **Testes:** Concluído
- **Detalhes:** Formato instável (Emojis e espaços posicionalmente ruidosos). Função: Injetar `category_id` (Teacher Forcing).

---

