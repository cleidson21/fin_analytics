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


def validate_date(date_value: str) -> str:
    """Valida o formato YYYY-MM-DD e levanta erro HTTP padrão se falhar."""
    try:
        datetime.strptime(date_value, "%Y-%m-%d")
        return date_value
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Formato de data inválido. Use YYYY-MM-DD (ex: 2026-05-29).",
        ) from exc