import os
import sys

# Garante que o script pode rodar da raiz do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.repository import DatabaseManager
from app.api.deps import get_password_hash

def seed_admin():
    db = DatabaseManager()
    
    # Verifica se admin já existe
    existing = db.get_user_by_username("admin")
    if existing:
        print("Usuário admin já existe.")
        return

    print("Criando usuário admin...")
    hashed_password = get_password_hash("admin123")
    user_id = db.create_user(
        username="admin",
        email="admin@finanalytics.local",
        password_hash=hashed_password,
        role="ADMIN"
    )
    print(f"Usuário admin criado com sucesso (ID: {user_id}).")
    print("Credenciais de acesso:")
    print("  Username: admin")
    print("  Password: admin123")

if __name__ == "__main__":
    seed_admin()
