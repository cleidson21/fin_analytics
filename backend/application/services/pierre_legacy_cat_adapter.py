from typing import Optional, List
from uuid import UUID

from backend.domain.entities.category import Category
# PierreImportService expects save() method which is in SQLAlchemyCategoryRepository

def _entity_to_legacy_dict(cat: Category) -> dict:
    return {
        "provider": "pierre",
        "name": cat.name,
        "normalized_name": cat.slug
    }

class PierreLegacyCategoryAdapter:
    def __init__(self):
        from backend.domains.pierre.repository import CategoryRepository as LegacyCatRepo
        from backend.database.session import SessionLocal
        self._legacy_repo = LegacyCatRepo()
        self._SessionLocal = SessionLocal

    async def save(self, category: Category) -> Category:
        cat_dict = _entity_to_legacy_dict(category)
        db = self._SessionLocal()
        try:
            self._legacy_repo.insert_if_not_exists(db, cat_dict)
            db.commit()
        finally:
            db.close()
        return category
