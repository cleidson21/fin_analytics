from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from backend.domains.pierre.pipeline import PierreImportPipeline

router = APIRouter(prefix="/pierre", tags=["Pierre Integration"])

class ImportRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None

@router.post("/import")
async def import_pierre_data(request: ImportRequest):
    try:
        pipeline = PierreImportPipeline()
        result = await pipeline.run(start_date=request.start_date, end_date=request.end_date)
        
        return {
            "success": True,
            "accounts": result.get("accounts", 0),
            "categories": result.get("categories", 0),
            "transactions": result.get("transactions", 0)
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        error_str = str(e).lower()
        if "authentication error" in error_str or "unauthorized" in error_str or "401" in error_str:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
