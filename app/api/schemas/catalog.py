from pydantic import BaseModel


class CatalogResponse(BaseModel):
    categories: list[str]
    natures: list[str]
    accounts: list[str]