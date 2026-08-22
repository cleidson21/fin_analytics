import httpx
from typing import Optional
from backend.core.config import settings

class PierreHTTPClient:
    def __init__(self, base_url: Optional[str] = None, timeout: float = 30.0):
        self.base_url = base_url or "https://www.pierre.finance/tools/api"
        self.timeout = timeout
        api_key = settings.PIERRE_API_KEY
        if not api_key:
            raise ValueError("PIERRE_API_KEY environment variable is not set. Please configure it in .env")
            
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }

    async def get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise Exception("Authentication error: Invalid Pierre API key") from e
                raise Exception(f"HTTP error: {e.response.status_code} - {e.response.text}") from e
                
            except httpx.TimeoutException as e:
                raise Exception("Timeout error: Pierre API took too long to respond") from e
                
            except httpx.RequestError as e:
                raise Exception(f"Connection error: Failed to reach Pierre API - {str(e)}") from e

    async def get_installments(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> dict:
        """
        Retorna o payload original de parcelamentos da Pierre Finance.
        Opcionalmente, pode ser filtrado por data.
        """
        params = {}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
            
        return await self.get("get-installments", params=params)
