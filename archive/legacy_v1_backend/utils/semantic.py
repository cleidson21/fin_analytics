import re
import unicodedata


def normalize_description(desc: str) -> str:
    """Limpa ruídos bancarios, consolida padroes de PIX e remove IDs."""
    if not desc:
        return ""

    normalized = unicodedata.normalize("NFKD", str(desc))
    clean = "".join([c for c in normalized if not unicodedata.combining(c)])
    clean = clean.upper()

    clean = clean.replace("*", " ")

    clean = re.sub(r"(TRANSFERENCIA ENVIADA PELO PIX).*$", r"\1", clean)
    clean = re.sub(r"(TRANSFERENCIA RECEBIDA PELO PIX).*$", r"\1", clean)
    clean = re.sub(r"(TRANSFERENCIA RECEBIDA) -.*$", r"\1", clean)

    clean = re.sub(r"\s+", " ", clean).strip()

    return clean