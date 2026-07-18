from backend.domains.imports.readers.base import BaseCsvReader
from backend.domains.imports.dto import ImportSource

class NubankContaReader(BaseCsvReader):
    """Reader responsável por extrair dados do CSV da Conta Nubank."""
    source_system = ImportSource.NUBANK_CONTA
