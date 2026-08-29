"""
Parser MyProfit — suporta os três tipos de exportação:
  - MYPROFIT_ATIVOS:    carteira atual (Ativo, Qtd, Preço médio, Setor, ...)
  - MYPROFIT_EVOLUCAO:  evolução patrimonial mensal (Data, Patrimônio, ...)
  - MYPROFIT_PROVENTOS: histórico de proventos (Ativo, Recebido, Tipo, Data pgto., ...)

Regras comuns a todos os tipos:
  - Identifica colunas pelo nome/header, nunca pela posição.
  - Tolera ordem diferente de colunas, colunas extras, BOM, encoding Windows,
    separador ; ou , detectável automaticamente, valores PT-BR.
  - O nome físico do arquivo NÃO é utilizado como critério de identificação.
"""

import csv
import io
import unicodedata
from typing import Dict, List, Any, Optional, Tuple


# --------------------------------------------------------------------------
# Definição de colunas por tipo
# --------------------------------------------------------------------------

# Colunas identificadas pelo header normalizado (sem acentos, lowercase, underscores)
MYPROFIT_ATIVOS_REQUIRED = {"ativo", "qtd"}
MYPROFIT_ATIVOS_OPTIONAL = {"preco_medio", "setor", "total_investido", "total_atual"}
MYPROFIT_ATIVOS_IGNORED = {
    "preco_de_aquisicao", "operacao",
    "preco_atual", "ganho", "pct_ganho",
    "cambio_compra", "pct_patrimonio"
}

MYPROFIT_EVOLUCAO_REQUIRED = {"data", "patrimonio"}
MYPROFIT_PROVENTOS_REQUIRED = {"ativo", "recebido", "tipo", "data_pgto"}


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _normalize_header(header: str) -> str:
    """Normaliza um header: remove acentos, lowercase, underscores, strip."""
    h = unicodedata.normalize("NFKD", header).encode("ASCII", "ignore").decode("utf-8")
    return (
        h.strip()
        .lower()
        .replace(" ", "_")
        .replace(".", "")
        .replace("%", "pct")
        .replace("/", "_")
        .replace("-", "_")
    )


def parse_pt_br_amount(val: str) -> Optional[float]:
    """Converte valor PT-BR (R$ 1.033,31 ou -18,63 ou 51,43 %) para float."""
    if not val or val.strip() in ("", "-"):
        return None
    val = val.strip().replace("R$", "").replace("%", "").strip()
    if not val:
        return None

    is_negative = False
    if val.startswith("-"):
        is_negative = True
        val = val[1:].strip()

    if "," in val and "." in val:
        # PT-BR: 1.033,31 → ponto é milhar, vírgula é decimal
        if val.rfind(",") > val.rfind("."):
            val = val.replace(".", "").replace(",", ".")
        else:
            val = val.replace(",", "")
    elif "," in val:
        val = val.replace(",", ".")

    try:
        result = float(val)
        return -result if is_negative else result
    except ValueError:
        return None


def _is_total_row(row: Dict[str, Any]) -> bool:
    """
    Detecta a linha de totais do MyProfit.
    Exemplos de linhas que devem ser ignoradas:
      "26 ativos",,Total:,,,R$ 105.611,25,...
    Heurística: o campo 'ativo' contém ' ativos' ou o campo normalizado
    de ticker termina com ' ativos'.
    """
    ativo = (row.get("ativo") or "").strip().lower()
    return (
        "ativos" in ativo
        or ativo.endswith("ativo")
        or "total:" in (row.get("preco_de_aquisicao") or "").lower()
        or "total" in ativo
    )


# --------------------------------------------------------------------------
# Classe principal
# --------------------------------------------------------------------------

class MyProfitParser:
    """
    Parser unificado para os três formatos de exportação MyProfit.

    Uso:
        parser = MyProfitParser(file_content)
        rows, report = parser.parse_ativos()
    """

    def __init__(self, file_content: bytes):
        try:
            self.raw_content = file_content.decode("utf-8-sig")  # BOM UTF-8
        except UnicodeDecodeError:
            self.raw_content = file_content.decode("iso-8859-1")

        # Auto-detectar delimitador
        first_line = self.raw_content.split("\n")[0] if self.raw_content else ""
        self.delimiter = ";" if first_line.count(";") > first_line.count(",") else ","

    def _read_rows(self) -> Tuple[List[str], List[Dict[str, str]]]:
        """
        Lê o CSV, normaliza headers, retorna (headers_normalizados, rows_brutas).
        """
        reader = csv.DictReader(io.StringIO(self.raw_content), delimiter=self.delimiter)
        if not reader.fieldnames:
            return [], []

        normalized_headers = [_normalize_header(h) for h in reader.fieldnames]
        reader.fieldnames = normalized_headers

        rows = []
        for row in reader:
            cleaned = {}
            for k, v in row.items():
                if not k:
                    continue
                val = v.strip() if v else None
                if val == "-":
                    val = None
                cleaned[k] = val
            if any(cleaned.values()):
                rows.append(cleaned)

        return normalized_headers, rows

    def validate_headers(self, source_type: str) -> Dict[str, Any]:
        """
        Valida se os headers do CSV são compatíveis com o source_type selecionado.
        Retorna relatório com colunas presentes, ausentes, opcionais e ignoradas.
        Lança ValueError se colunas obrigatórias estiverem ausentes.
        """
        headers, _ = self._read_rows()
        header_set = set(headers)

        if source_type == "MYPROFIT_ATIVOS":
            required = MYPROFIT_ATIVOS_REQUIRED
            optional = MYPROFIT_ATIVOS_OPTIONAL
            ignored = MYPROFIT_ATIVOS_IGNORED
        elif source_type == "MYPROFIT_EVOLUCAO":
            required = MYPROFIT_EVOLUCAO_REQUIRED
            optional = set()
            ignored = set()
        elif source_type == "MYPROFIT_PROVENTOS":
            required = MYPROFIT_PROVENTOS_REQUIRED
            optional = set()
            ignored = set()
        else:
            raise ValueError(f"Tipo desconhecido: {source_type}")

        missing = required - header_set
        present_required = required & header_set
        present_optional = optional & header_set
        present_ignored = header_set - required - optional  # tudo mais é ignorado

        report = {
            "required_columns": sorted(present_required),
            "optional_columns": sorted(present_optional),
            "missing_columns": sorted(missing),
            "ignored_columns": sorted(present_ignored),
            "errors": [],
            "warnings": [],
        }

        if missing:
            report["errors"].append(
                f"Colunas obrigatórias ausentes para {source_type}: {', '.join(sorted(missing))}. "
                f"Verifique se o tipo selecionado corresponde ao arquivo."
            )

        return report

    def parse(self) -> List[Dict[str, Any]]:
        """
        Modo genérico: normaliza headers e retorna todas as linhas.
        Usado para compatibilidade com código legado (UploadImportUseCase).
        """
        _, rows = self._read_rows()
        return rows

    def parse_ativos(self) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Parseia CSV do tipo MYPROFIT_ATIVOS.
        Valida headers obrigatórios, ignora linha de totais.
        Retorna (linhas_válidas, relatório).
        """
        report = self.validate_headers("MYPROFIT_ATIVOS")
        if report["errors"]:
            return [], report

        _, rows = self._read_rows()

        valid_rows = []
        skipped_total = 0

        for row in rows:
            # Ignorar linha de totais do MyProfit
            if _is_total_row(row):
                skipped_total += 1
                continue

            ticker = (row.get("ativo") or "").strip()
            if not ticker:
                report["warnings"].append("Linha ignorada: ticker vazio.")
                continue

            qty_raw = row.get("qtd")
            qty = parse_pt_br_amount(qty_raw or "") if qty_raw else None
            sector = (row.get("setor") or "").strip() or None

            if qty is None and sector != "RDB":
                report["warnings"].append(
                    f"Ativo '{ticker}' ignorado: quantidade '{qty_raw}' não é um número válido e não é RDB."
                )
                continue

            avg_price = parse_pt_br_amount(row.get("preco_medio") or "")
            total_investido = parse_pt_br_amount(row.get("total_investido") or "")
            total_atual = parse_pt_br_amount(row.get("total_atual") or "")

            valid_rows.append({
                "ticker": ticker,
                "quantity": qty,
                "avg_price": avg_price,
                "sector": sector,
                "total_investido": total_investido,
                "total_atual": total_atual,
            })

        if skipped_total > 0:
            report["warnings"].append(
                f"{skipped_total} linha(s) de totais do MyProfit detectada(s) e ignorada(s)."
            )

        report["total_rows"] = len(rows)
        report["valid_rows"] = len(valid_rows)

        return valid_rows, report
