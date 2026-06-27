from backend.domains.imports.readers.base import BaseCsvReader

class NubankFaturaReader(BaseCsvReader):
    """Reader responsável por extrair dados do CSV da Fatura Nubank."""
    source_system = "NUBANK_FATURA_CSV"
