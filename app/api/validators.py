from datetime import datetime

from fastapi import HTTPException


def validate_month(month: str) -> str:
    """Valida o formato YYYY-MM e levanta erro HTTP padrão se falhar."""
    try:
        datetime.strptime(month, "%Y-%m")
        return month
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Formato de mês inválido. Use YYYY-MM (ex: 2026-05).",
        ) from exc