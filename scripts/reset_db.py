import sys
import os

# Adiciona a raiz do projeto no path para encontrar o módulo backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.config import settings
from backend.database.disposable import disposable_script_session
from sqlalchemy import text

def reset_database():
    """
    Limpa todas as tabelas de negócio (dados transacionais),
    preservando tabelas de domínio (categories, assets) e sistema (users).
    """
    with disposable_script_session(settings.DATABASE_URL) as db:
        tables_to_clear = [
            "import_artifacts",
            "import_runs",
            "position_snapshots",
            "portfolio_snapshots",
            "dividends",
            "transactions"
        ]

        print("Iniciando limpeza do banco de dados (Homologação H1.3+)...")

        try:
            # Em SQLite, foreign keys são desativadas por padrão, mas é bom garantir
            db.execute(text("PRAGMA foreign_keys = OFF;"))

            for table in tables_to_clear:
                db.execute(text(f"DELETE FROM {table};"))
                print(f" -> Tabela '{table}' limpa.")

            db.execute(text("PRAGMA foreign_keys = ON;"))
            db.commit()

            # Opcional: Vacum para limpar espaço físico
            db.execute(text("VACUUM;"))

            print("\n[OK] Banco de dados limpo com sucesso! Pronto para nova homologação E2E.")
        except Exception as e:
            db.rollback()
            print(f"\n[ERRO] Erro ao limpar o banco de dados: {e}")

if __name__ == "__main__":
    reset_database()
