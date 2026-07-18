from backend.domains.imports.readers.base import BaseCsvReader
from backend.domains.imports.dto import ImportSource

class MyProfitProventosReader(BaseCsvReader):
    """
    Leitor dedicado ao arquivo CSV de Proventos do MyProfit.
    """
    
    @property
    def source_system(self) -> ImportSource:
        return ImportSource.MYPROFIT_PROVENTOS
