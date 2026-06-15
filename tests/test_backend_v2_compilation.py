from app.core.db import get_db, engine
from app.core.dependencies import get_transaction_repo, get_position_repo
from app.models.core_finance import Transaction
from app.models.wealth import Position
from app.models.governance import ImportRun
from app.models.ai_layer import Rule

def test_compilation():
    print("Models and Repositories imported successfully!")
    db = next(get_db())
    print("Database connected.")
    
    # Test a simple query to ensure ORM mapping matches the schema
    try:
        import_runs = db.query(ImportRun).limit(1).all()
        print("ORM query to ImportRun succeeded.")
    except Exception as e:
        print(f"Failed to query ImportRun: {e}")
        return False
        
    return True

if __name__ == "__main__":
    test_compilation()
