from dataclasses import asdict
from datetime import date
from decimal import Decimal

import pytest

from backend.domains.smart_context.recurring_income import (
    SIGNATURE_VERSION,
    RecurringIncomeCandidateState,
    RecurringIncomeDirection,
    RecurringIncomeEvidenceEngine,
    RecurringIncomeObservation,
    RecurringIncomeRiskFlag,
    build_source_signature,
    canonical_signature_payload,
    evidence_window_start,
    normalize_recurring_description,
)


def _observation(
    occurred_on: date,
    amount: str,
    *,
    key: str,
    description: str = "Pagamento mensal 2026",
    provider: str = "pierre",
    account_scope: str = "sha256:account-a",
    currency: str = "BRL",
    risk_flags: tuple[RecurringIncomeRiskFlag, ...] = (),
) -> RecurringIncomeObservation:
    return RecurringIncomeObservation(
        source_record_key=key,
        provider=provider,
        account_scope=account_scope,
        currency=currency,
        direction=RecurringIncomeDirection.CREDIT,
        description=description,
        amount=Decimal(amount),
        occurred_on=occurred_on,
        risk_flags=risk_flags,
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  PAGAMENTO   Mensal  ", "pagamento mensal"),
        ("PAGAMENTO\t\nMENSAL", "pagamento mensal"),
        ("\uff30\uff21\uff27\uff21\uff2d\uff25\uff2e\uff34\uff2f  \uff12\uff10\uff12\uff16", "pagamento 2026"),
        ("Sal\u00e1rio M\u00eas", "sal\u00e1rio m\u00eas"),
    ],
)
def test_normalization_v1_is_conservative_and_deterministic(raw, expected):
    assert normalize_recurring_description(raw) == expected


def test_normalization_v1_preserves_digit_and_accent_differences():
    assert normalize_recurring_description("Fonte 10") != normalize_recurring_description(
        "Fonte 11"
    )
    assert normalize_recurring_description("salario") != normalize_recurring_description(
        "sal\u00e1rio"
    )


def test_signature_v1_has_an_explicit_payload_and_golden_vector():
    payload = canonical_signature_payload(
        provider="pierre",
        account_scope="sha256:account-scope",
        currency="BRL",
        direction=RecurringIncomeDirection.CREDIT,
        normalized_description="sal\u00e1rio mensal",
    )
    signature = build_source_signature(
        provider="pierre",
        account_scope="sha256:account-scope",
        currency="BRL",
        direction=RecurringIncomeDirection.CREDIT,
        normalized_description="sal\u00e1rio mensal",
    )

    assert payload == (
        '[1,"pierre","sha256:account-scope","BRL","CREDIT",'
        '"sal\u00e1rio mensal"]'
    )
    assert signature == (
        "sha256:053a5b44b2287cb0f497139793970e3c9b499fe11b14274527ab8940ea539350"
    )


@pytest.mark.parametrize(
    "changed",
    [
        {"provider": "other"},
        {"account_scope": "sha256:account-b"},
        {"currency": "USD"},
        {"normalized_description": "pagamento mensal 2027"},
    ],
)
def test_signature_changes_for_each_locked_identity_component(changed):
    base = {
        "provider": "pierre",
        "account_scope": "sha256:account-a",
        "currency": "BRL",
        "direction": RecurringIncomeDirection.CREDIT,
        "normalized_description": "pagamento mensal 2026",
    }

    assert build_source_signature(**base) != build_source_signature(**{**base, **changed})


def test_cosmetic_description_variations_generate_the_same_signature():
    descriptions = (
        " PAGAMENTO  MENSAL 2026 ",
        "pagamento mensal 2026",
        "\uff30\uff21\uff27\uff21\uff2d\uff25\uff2e\uff34\uff2f\t\uff2d\uff25\uff2e\uff33\uff21\uff2c 2026",
    )
    signatures = {
        build_source_signature(
            provider="pierre",
            account_scope="sha256:account-a",
            currency="BRL",
            direction=RecurringIncomeDirection.CREDIT,
            normalized_description=normalize_recurring_description(description),
        )
        for description in descriptions
    }

    assert len(signatures) == 1


@pytest.mark.parametrize(
    ("as_of_date", "expected"),
    [
        (date(2026, 5, 31), date(2025, 12, 1)),
        (date(2026, 1, 31), date(2025, 8, 1)),
        (date(2024, 2, 29), date(2023, 9, 1)),
    ],
)
def test_six_month_window_start_crosses_year_and_leap_boundaries(
    as_of_date,
    expected,
):
    assert evidence_window_start(as_of_date) == expected


def test_three_distinct_non_consecutive_months_are_a_candidate():
    observations = (
        _observation(date(2026, 1, 31), "1000.00", key="1"),
        _observation(date(2026, 3, 1), "2000.00", key="2"),
        _observation(date(2026, 5, 15), "3000.00", key="3"),
    )

    candidates = RecurringIncomeEvidenceEngine().detect(
        observations,
        as_of_date=date(2026, 5, 20),
    )

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.classification_state is RecurringIncomeCandidateState.DETECTED_CANDIDATE
    assert candidate.signature_version == SIGNATURE_VERSION
    assert candidate.observed_months == ("2026-01", "2026-03", "2026-05")
    assert candidate.distinct_month_count == 3
    assert candidate.current_month_is_partial is True
    assert candidate.includes_current_month is True


def test_end_and_start_of_month_shift_uses_calendar_coverage_only():
    observations = (
        _observation(date(2026, 1, 31), "1000.00", key="1"),
        _observation(date(2026, 2, 1), "1050.00", key="2"),
        _observation(date(2026, 3, 31), "900.00", key="3"),
    )

    candidate = RecurringIncomeEvidenceEngine().detect(
        observations,
        as_of_date=date(2026, 3, 31),
    )[0]

    assert candidate.distinct_month_count == 3
    assert candidate.observed_months == ("2026-01", "2026-02", "2026-03")


@pytest.mark.parametrize(
    "dates",
    [
        (date(2026, 3, 1), date(2026, 3, 10), date(2026, 3, 20)),
        (date(2026, 3, 1), date(2026, 4, 1)),
    ],
)
def test_same_month_repetition_or_two_months_do_not_pass_the_gate(dates):
    observations = tuple(
        _observation(value, "1000.00", key=str(index))
        for index, value in enumerate(dates)
    )

    assert (
        RecurringIncomeEvidenceEngine().detect(
            observations,
            as_of_date=date(2026, 5, 31),
        )
        == ()
    )


def test_same_month_occurrences_count_once_for_coverage_but_all_for_evidence():
    observations = (
        _observation(date(2026, 3, 1), "100.00", key="1"),
        _observation(date(2026, 3, 31), "200.00", key="2"),
        _observation(date(2026, 4, 30), "300.00", key="3"),
        _observation(date(2026, 5, 1), "400.00", key="4"),
    )

    candidate = RecurringIncomeEvidenceEngine().detect(
        observations,
        as_of_date=date(2026, 5, 31),
    )[0]

    assert candidate.distinct_month_count == 3
    assert candidate.occurrence_count == 4
    assert tuple(item.occurrence_count for item in candidate.monthly_occurrences) == (
        2,
        1,
        1,
    )
    assert candidate.current_month_is_partial is False


def test_amount_variability_does_not_suppress_exact_decimal_evidence():
    observations = (
        _observation(date(2026, 1, 5), "0.10", key="1"),
        _observation(date(2026, 2, 5), "100000000000.00", key="2"),
        _observation(date(2026, 3, 5), "10.000", key="3"),
        _observation(date(2026, 4, 5), "20.00", key="4"),
    )

    candidate = RecurringIncomeEvidenceEngine().detect(
        observations,
        as_of_date=date(2026, 4, 30),
    )[0]

    assert candidate.minimum_received_amount == Decimal("0.10")
    assert candidate.maximum_received_amount == Decimal("100000000000.00")
    assert candidate.typical_received_amount == Decimal("15.000")
    assert candidate.median_absolute_deviation == Decimal("9.950")
    assert type(candidate.typical_received_amount) is Decimal


def test_odd_median_and_mad_are_exact_decimal_values():
    observations = (
        _observation(date(2026, 1, 1), "1.00", key="1"),
        _observation(date(2026, 2, 1), "2.00", key="2"),
        _observation(date(2026, 3, 1), "100.00", key="3"),
    )

    candidate = RecurringIncomeEvidenceEngine().detect(
        observations,
        as_of_date=date(2026, 3, 31),
    )[0]

    assert candidate.typical_received_amount == Decimal("2.00")
    assert candidate.median_absolute_deviation == Decimal("1.00")


def test_observation_outside_the_window_does_not_affect_current_evidence():
    observations = (
        _observation(date(2025, 11, 30), "999.00", key="old"),
        _observation(date(2025, 12, 1), "100.00", key="1"),
        _observation(date(2026, 1, 31), "200.00", key="2"),
        _observation(date(2026, 2, 1), "300.00", key="3"),
        _observation(date(2026, 6, 1), "777.00", key="future"),
    )

    candidate = RecurringIncomeEvidenceEngine().detect(
        observations,
        as_of_date=date(2026, 5, 31),
    )[0]

    assert candidate.window_start == date(2025, 12, 1)
    assert candidate.window_end == date(2026, 5, 31)
    assert candidate.first_occurrence_date == date(2025, 12, 1)
    assert candidate.latest_occurrence_date == date(2026, 2, 1)
    assert candidate.occurrence_count == 3


def test_one_of_three_occurrences_outside_window_leaves_insufficient_history():
    observations = (
        _observation(date(2025, 11, 30), "100.00", key="old"),
        _observation(date(2025, 12, 1), "200.00", key="1"),
        _observation(date(2026, 1, 1), "300.00", key="2"),
    )

    assert (
        RecurringIncomeEvidenceEngine().detect(
            observations,
            as_of_date=date(2026, 5, 31),
        )
        == ()
    )


def test_multiple_sources_and_currencies_remain_separate_and_ordered():
    observations = tuple(
        _observation(date(2026, month, 5), "100.00", key=f"a-{month}")
        for month in (1, 2, 3)
    ) + tuple(
        _observation(
            date(2026, month, 10),
            "50.00",
            key=f"b-{month}",
            account_scope="sha256:account-b",
            currency="USD",
        )
        for month in (2, 3, 4)
    )

    candidates = RecurringIncomeEvidenceEngine().detect(
        observations,
        as_of_date=date(2026, 4, 30),
    )

    assert len(candidates) == 2
    assert [candidate.currency for candidate in candidates] == ["USD", "BRL"]
    assert candidates[0].latest_occurrence_date > candidates[1].latest_occurrence_date
    assert candidates[0].source_signature != candidates[1].source_signature


def test_equal_latest_dates_use_source_signature_as_stable_tie_break():
    observations = tuple(
        _observation(date(2026, month, 5), "100.00", key=f"a-{month}")
        for month in (1, 2, 3)
    ) + tuple(
        _observation(
            date(2026, month, 5),
            "200.00",
            key=f"b-{month}",
            account_scope="sha256:account-b",
        )
        for month in (1, 2, 3)
    )

    candidates = RecurringIncomeEvidenceEngine().detect(
        observations,
        as_of_date=date(2026, 3, 31),
    )

    assert [item.source_signature for item in candidates] == sorted(
        item.source_signature for item in candidates
    )


def test_transfer_ambiguity_is_evidence_not_exclusion_or_confidence():
    observations = tuple(
        _observation(
            date(2026, month, 5),
            "1000.00",
            key=str(month),
            risk_flags=(RecurringIncomeRiskFlag.TRANSFER_AMBIGUITY,),
        )
        for month in (1, 2, 3)
    )

    candidate = RecurringIncomeEvidenceEngine().detect(
        observations,
        as_of_date=date(2026, 3, 31),
    )[0]
    candidate_fields = asdict(candidate)

    assert candidate.risk_flags == (RecurringIncomeRiskFlag.TRANSFER_AMBIGUITY,)
    assert "confidence" not in candidate_fields
    assert "description" not in candidate_fields
    assert candidate.candidate_id.startswith("ric_v1_")
