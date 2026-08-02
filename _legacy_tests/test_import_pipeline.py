import pytest
from unittest.mock import patch, MagicMock
from backend.domains.investments.services.import_service import ImportService
from backend.domains.investments.dto import TradeDTO

class DummyTradeRepo:
    def __init__(self):
        self.db = set()
    
    def save_idempotent(self, session, trade):
        if trade.idempotency_hash in self.db:
            return False
        self.db.add(trade.idempotency_hash)
        return True

@patch('backend.domains.investments.services.import_service.TradeRepository', DummyTradeRepo)
def test_import_pipeline_idempotency():
    db = MagicMock()
    service = ImportService(db)
    
    # Needs to bypass actual init inside ImportService if we mock it at class level, 
    # but since we patched it, ImportService will instantiate DummyTradeRepo.
    # We can inject it manually just in case:
    repo = DummyTradeRepo()
    service.trade_repo = repo
    
    csv_content = b"Ticker,Data,Tipo,Quantidade,Preco,Corretora\nPETR4,2023-01-10,COMPRA,100,25.50,XP\nVALE3,2023-01-15,VENDA,50,70.00,NU"
    
    # First Import
    report1 = service.process_import(csv_content, "test.csv", "CEI")
    assert report1.success == True
    assert report1.rows_persisted == 2
    assert report1.duplicates_detected == 0
    
    # Second Import (Idempotent check)
    report2 = service.process_import(csv_content, "test.csv", "CEI")
    # Due to hash matching, they will be ignored
    assert report2.success == True # it is still success since file was processed without crash, just duplicates
    assert report2.rows_persisted == 0
    assert report2.duplicates_detected == 2
