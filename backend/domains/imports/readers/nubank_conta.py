from backend.domains.imports.readers.base import BaseCsvReader

class NubankContaReader(BaseCsvReader):
    """Reader responsável por extrair dados do CSV da Conta Nubank."""
    source_system = "NUBANK_CONTA_CSV"
