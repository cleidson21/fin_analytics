from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.dependencies.auth import get_db_session
from backend.core.container import get_jwt_service, get_user_repository

router = APIRouter(prefix="/dev", tags=["Development"])

@router.get("/status")
async def get_status(session: AsyncSession = Depends(get_db_session)):
    status = {
        "database": "error",
        "bootstrap": "error",
        "admin_exists": False,
        "jwt": "error"
    }
    
    try:
        await session.execute(text("SELECT 1"))
        status["database"] = "ok"
        status["bootstrap"] = "ok"
    except Exception:
        pass
    
    try:
        user_repo = get_user_repository(session)
        admin = await user_repo.get_by_email("admin")
        if admin:
            status["admin_exists"] = True
    except Exception:
        pass
        
    try:
        jwt_svc = get_jwt_service()
        if jwt_svc:
            status["jwt"] = "ok"
    except Exception:
        pass
        
    return status
