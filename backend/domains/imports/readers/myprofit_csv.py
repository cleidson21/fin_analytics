from backend.domains.imports.readers.base import BaseCsvReader

class MyProfitProventosReader(BaseCsvReader):
    """
    Leitor dedicado ao arquivo CSV de Proventos do MyProfit.
    """
    
    @property
    def source_system(self) -> str:
        return "MYPROFIT"
