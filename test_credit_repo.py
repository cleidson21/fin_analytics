from sqlalchemy import text, create_engine
from backend.domains.credit.repository import CreditRepository

def run_tests():
    engine = create_engine("sqlite:///database/fin_analytics_v3.db")
    with engine.connect() as db:
        repo = CreditRepository(db)
        
        print("Testing get_installments_dashboard...")
        try:
            installments = repo.get_installments_dashboard("2026-06")
            print("Success! Result keys:", installments.model_dump().keys())
            print("Active Installments:", installments.active_installments)
            print("Finished Installments:", installments.finished_installments)
            print("Global Estimated:", installments.global_estimated)
        except Exception as e:
            print("Error testing installments:", e)

        print("\nTesting get_subscriptions_dashboard...")
        try:
            subscriptions = repo.get_subscriptions_dashboard("2026-06")
            print("Success! Result keys:", subscriptions.model_dump().keys())
            print("Active Count:", subscriptions.active_count)
            print("Monthly Total:", subscriptions.monthly_total)
        except Exception as e:
            print("Error testing subscriptions:", e)

if __name__ == "__main__":
    run_tests()
