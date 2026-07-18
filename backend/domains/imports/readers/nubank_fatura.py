from backend.domains.imports.readers.base import BaseCsvReader
from backend.domains.imports.dto import ImportSource

class NubankFaturaReader(BaseCsvReader):
    """Reader responsável por extrair dados do CSV da Fatura Nubank."""
    source_system = ImportSource.NUBANK_FATURA
