from typing import Optional
from backend.domains.pierre.connector import PierreConnector
from backend.domains.pierre.mapper import PierreMapper
from backend.domains.pierre.service import (
    AccountService,
    TransactionService,
    CategoryService
)

class PierreImportPipeline:
    def __init__(self):
        self.connector = PierreConnector()
        self.mapper = PierreMapper()
        self.account_service = AccountService()
        self.transaction_service = TransactionService()
        self.category_service = CategoryService()

    async def run(self, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """
        Executes the import pipeline: Fetch -> Map -> Persist
        """
        payload = await self.connector.get_transactions(start_date=start_date, end_date=end_date)
        
        if not payload or not payload.get("success"):
            raise ValueError("Payload indicates failure or is empty")

        transactions_raw = payload.get("data", [])

        count_acc = 0
        count_cat = 0
        count_tx = 0

        for raw_tx in transactions_raw:
            try:
                account_data, tx_data, category_data = self.mapper.map_transaction(raw_tx)
            except Exception as e:
                raise RuntimeError(f"Erro de mapeamento para a transacao {raw_tx.get('id')}: {e}") from e

            try:
                self.account_service.save(account_data)
                self.category_service.save_if_not_exists(category_data)
                self.transaction_service.save(tx_data)
                
                count_acc += 1
                count_cat += 1
                count_tx += 1
            except Exception as e:
                raise RuntimeError(f"Erro de persistencia para a transacao {tx_data.get('external_id')}: {e}") from e

        return {
            "accounts": count_acc,
            "categories": count_cat,
            "transactions": count_tx
        }
