from typing import Optional, Dict, Any
from backend.domains.pierre.client import PierreHTTPClient

class PierreConnector:
    def __init__(self):
        self.client = PierreHTTPClient()

    async def get_transactions(
        self, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None, 
        format_type: str = "raw"
    ) -> Dict[str, Any]:
        """
        Fetches the raw transactions payload from Pierre API.
        start_date/end_date should be 'YYYY-MM-DD'.
        """
        params = {"format": format_type}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
            
        return await self.client.get("/get-transactions", params=params)
