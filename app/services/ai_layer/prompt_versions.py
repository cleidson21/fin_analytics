from sqlalchemy.orm import Session
from app.models.ai_layer import PromptVersion
from datetime import datetime

class PromptVersionService:
    def __init__(self, db: Session):
        self.db = db

    def get_active_version(self) -> PromptVersion:
        """Busca a versão ativa vigente."""
        return self.db.query(PromptVersion).filter(PromptVersion.active == 1).first()

    def activate_version(self, version_id: str) -> PromptVersion:
        """
        Ativa a versão especificada e desativa qualquer outra versão.
        Impede duas versões ativas.
        """
        version_to_activate = self.db.query(PromptVersion).filter(PromptVersion.id == version_id).first()
        if not version_to_activate:
            raise ValueError("PromptVersion not found")

        # Deactivate all others
        active_versions = self.db.query(PromptVersion).filter(PromptVersion.active == 1).all()
        for v in active_versions:
            if v.id != version_id:
                v.active = 0
        
        version_to_activate.active = 1
        
        self.db.commit()
        self.db.refresh(version_to_activate)
        return version_to_activate

    def deactivate_version(self, version_id: str) -> PromptVersion:
        """Desativa a versão especificada."""
        version = self.db.query(PromptVersion).filter(PromptVersion.id == version_id).first()
        if not version:
            raise ValueError("PromptVersion not found")
            
        version.active = 0
        self.db.commit()
        self.db.refresh(version)
        return version
