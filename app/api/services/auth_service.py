from database.financial_repository import FinancialRepository

class AuthService:
    def __init__(self):
        self.repo = FinancialRepository()

    def get_user_by_username(self, username: str):
        return self.repo.get_user_by_username(username)

    def create_user(self, username: str, email: str, password_hash: str, role: str = 'VIEWER'):
        return self.repo.create_user(username, email, password_hash, role)
