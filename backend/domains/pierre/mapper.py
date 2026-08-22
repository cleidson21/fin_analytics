import json
from typing import Dict, Any, Tuple
from datetime import datetime
import unicodedata

def normalize_string(s: str) -> str:
    if not s:
        return ""
    s = str(s).lower().strip()
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

class PierreMapper:
    @staticmethod
    def map_transaction(raw_tx: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """
        Maps a raw Pierre transaction into Account, Transaction, and Category dictionaries.
        Returns a tuple: (account_data, transaction_data, category_data)
        """
        provider = "pierre"
        
        # 1. Map Account
        account_data = {
            "provider": provider,
            "external_id": raw_tx.get("account_id"),
            "name": raw_tx.get("account_name", "Unknown Account"),
            "type": raw_tx.get("account_type", "BANK"),
            "subtype": raw_tx.get("account_subtype"),
            "bank": raw_tx.get("item_bank_name"),
            "connector": raw_tx.get("connector_name"),
            "credit_metadata_json": json.dumps(raw_tx.get("account_credit_data")) if raw_tx.get("account_credit_data") else None
        }

        # 2. Map Category
        category_name = raw_tx.get("category")
        if not category_name:
            category_name = "Uncategorized"
        category_data = {
            "provider": provider,
            "name": category_name,
            "normalized_name": normalize_string(category_name)
        }

        # 3. Map Transaction
        merchant = raw_tx.get("merchant") or {}
        credit_card = raw_tx.get("credit_card_data") or {}
        payment = raw_tx.get("payment_data") or {}
        receiver = payment.get("receiver") or {}
        payer = payment.get("payer") or {}

        # Capture extra fields for extra_json
        mapped_keys = {
            "id", "account_id", "description", "original_description", 
            "category", "original_category", "amount", "currency_code", 
            "date", "status", "type", "merchant", "credit_card_data", 
            "payment_data", "manual_transaction", "account_name", 
            "account_type", "account_subtype", "connector_name", 
            "item_bank_name", "account_credit_data",
            # Additional Pierre payload fields (only keep those explicitly mapped to prevent duplication in extra_json)
            "bill_id"
        }
        extra_fields = {k: v for k, v in raw_tx.items() if k not in mapped_keys}
        
        date_str = raw_tx.get("date")
        if date_str:
            date_val = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        else:
            date_val = datetime.now()

        purchase_date_str = credit_card.get("purchaseDate")
        purchase_date_val = None
        if purchase_date_str:
            purchase_date_val = datetime.fromisoformat(purchase_date_str.replace("Z", "+00:00"))

        transaction_data = {
            "provider": provider,
            "external_id": raw_tx.get("id"),
            "account_provider": provider,
            "account_external_id": raw_tx.get("account_id"),
            
            "description": raw_tx.get("description", "Sem descrição"),
            "original_description": raw_tx.get("original_description"),
            "category": category_name,
            "original_category": raw_tx.get("original_category"),
            "amount": raw_tx.get("amount", 0.0),
            "currency": raw_tx.get("currency_code", "BRL"),
            "date": date_val,
            "status": raw_tx.get("status", "POSTED"),
            "type": raw_tx.get("type", "DEBIT"),
            
            "merchant_name": merchant.get("name"),
            "bill_id": credit_card.get("billId") or raw_tx.get("bill_id"),
            "installment_number": credit_card.get("installmentNumber"),
            "total_installments": credit_card.get("totalInstallments"),
            "purchase_date": purchase_date_val,
            "receiver_name": receiver.get("name"),
            "payer_name": payer.get("name"),
            
            "manual_transaction": raw_tx.get("manual_transaction", False),
            "extra_json": json.dumps(extra_fields) if extra_fields else None
        }

        return account_data, transaction_data, category_data
