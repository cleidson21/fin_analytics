from pydantic import BaseModel


class DividendHistory(BaseModel):
    month: str
    amount_received: str


class AssetAllocation(BaseModel):
    asset_class: str
    current_total: str


class NetWorthEvolution(BaseModel):
    month: str
    net_worth: str