from decimal import Decimal

from backend.application.dtos.profile_context_dto import (
    ProfileDeclaredContextResponseDTO,
)
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.domains.smart_context import DeclaredFinancialContext


def _serialize_decimal(value: Decimal) -> str:
    if type(value) is not Decimal or not value.is_finite():
        raise TypeError("Declared income must be a finite Decimal.")
    return str(value)


def map_profile_context_response(
    current_user: UserResponseDTO,
    context: DeclaredFinancialContext | None,
) -> ProfileDeclaredContextResponseDTO:
    """Map only approved identity and declared-context fields."""

    return ProfileDeclaredContextResponseDTO(
        name=current_user.name,
        email=current_user.email,
        declared_monthly_gross_income=(
            None
            if context is None or context.declared_monthly_gross_income is None
            else _serialize_decimal(context.declared_monthly_gross_income)
        ),
        semantic_type="DECLARED",
        source="USER_PROFILE",
        currency=None if context is None else context.currency,
        income_period=None if context is None else context.income_period,
        income_basis=None if context is None else context.income_basis,
        income_as_of_date=None if context is None else context.income_as_of_date,
        declared_at=None if context is None else context.declared_at,
        updated_at=None if context is None else context.updated_at,
    )
