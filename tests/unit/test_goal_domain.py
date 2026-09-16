"""
tests/unit/test_goal_domain.py

Testes do domínio de Goals:
  - GoalType enum (9 valores)
  - GoalStatus enum
  - Goal entity validações
  - Goal.progress_pct()
"""
import pytest
from datetime import date, timedelta
from uuid import uuid4

from backend.domain.enums.goal_type import GoalType
from backend.domain.enums.goal_status import GoalStatus
from backend.domain.entities.goal import Goal


# ------------------------------------------------------------------ #
#  GoalType — 9 valores                                               #
# ------------------------------------------------------------------ #

def test_goal_type_original_values():
    """Os 5 tipos originais devem existir e ter os valores corretos."""
    assert GoalType.EMERGENCY_RESERVE == "EMERGENCY_RESERVE"
    assert GoalType.RETIREMENT == "RETIREMENT"
    assert GoalType.TRAVEL == "TRAVEL"
    assert GoalType.PURCHASE == "PURCHASE"
    assert GoalType.CUSTOM == "CUSTOM"


def test_goal_type_new_values():
    """Os 4 novos tipos do Lote 10.1 devem existir."""
    assert GoalType.WEALTH_TARGET == "WEALTH_TARGET"
    assert GoalType.INVESTMENT_TARGET == "INVESTMENT_TARGET"
    assert GoalType.DIVIDEND_INCOME == "DIVIDEND_INCOME"
    assert GoalType.FINANCIAL_INDEPENDENCE == "FINANCIAL_INDEPENDENCE"


def test_goal_type_total_count():
    """GoalType deve ter exatamente 9 valores."""
    assert len(list(GoalType)) == 9


# ------------------------------------------------------------------ #
#  GoalStatus                                                         #
# ------------------------------------------------------------------ #

def test_goal_status_values():
    assert GoalStatus.ACTIVE == "ACTIVE"
    assert GoalStatus.ACHIEVED == "ACHIEVED"
    assert GoalStatus.PAUSED == "PAUSED"
    assert GoalStatus.CANCELLED == "CANCELLED"
    assert len(list(GoalStatus)) == 4


# ------------------------------------------------------------------ #
#  Goal entity — fábrica                                              #
# ------------------------------------------------------------------ #

def make_goal(**overrides):
    from datetime import datetime
    defaults = dict(
        id=uuid4(),
        user_id=uuid4(),
        name="Reserva de Emergência",
        target_amount=30000.0,
        goal_type=GoalType.EMERGENCY_RESERVE,
        status=GoalStatus.ACTIVE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    defaults.update(overrides)
    return Goal(**defaults)


# ------------------------------------------------------------------ #
#  Goal.validate() — campos obrigatórios                              #
# ------------------------------------------------------------------ #

def test_goal_validate_ok():
    """Goal válida não lança exceção."""
    goal = make_goal()
    goal.validate()  # Não deve lançar


def test_goal_validate_name_too_short():
    with pytest.raises(ValueError, match="3"):
        make_goal(name="AB").validate()


def test_goal_validate_name_too_long():
    with pytest.raises(ValueError, match="100"):
        make_goal(name="X" * 101).validate()


def test_goal_validate_target_amount_zero():
    with pytest.raises(ValueError, match="positive"):
        make_goal(target_amount=0).validate()


def test_goal_validate_target_amount_negative():
    with pytest.raises(ValueError, match="positive"):
        make_goal(target_amount=-500).validate()


def test_goal_validate_target_date_in_past():
    past = date.today() - timedelta(days=1)
    with pytest.raises(ValueError, match="future"):
        make_goal(target_date=past).validate()


def test_goal_validate_target_date_today_ok():
    """Data alvo = hoje é aceita (>= today)."""
    goal = make_goal(target_date=date.today())
    goal.validate()  # Não deve lançar


def test_goal_validate_target_date_future_ok():
    future = date.today() + timedelta(days=365)
    goal = make_goal(target_date=future)
    goal.validate()  # Não deve lançar


# ------------------------------------------------------------------ #
#  Goal.validate() — campos novos Lote 10.1                          #
# ------------------------------------------------------------------ #

def test_goal_validate_current_amount_zero_ok():
    """current_amount = 0 é válido (meta ainda não iniciada)."""
    goal = make_goal(current_amount=0.0)
    goal.validate()


def test_goal_validate_current_amount_positive_ok():
    goal = make_goal(current_amount=5000.0)
    goal.validate()


def test_goal_validate_current_amount_negative():
    with pytest.raises(ValueError, match="current_amount"):
        make_goal(current_amount=-100.0).validate()


def test_goal_validate_priority_valid():
    for p in [1, 2, 3, 4, 5]:
        goal = make_goal(priority=p)
        goal.validate()  # Não deve lançar


def test_goal_validate_priority_zero():
    with pytest.raises(ValueError, match="priority"):
        make_goal(priority=0).validate()


def test_goal_validate_priority_six():
    with pytest.raises(ValueError, match="priority"):
        make_goal(priority=6).validate()


def test_goal_validate_monthly_contribution_zero_ok():
    goal = make_goal(monthly_contribution=0.0)
    goal.validate()


def test_goal_validate_monthly_contribution_negative():
    with pytest.raises(ValueError, match="monthly_contribution"):
        make_goal(monthly_contribution=-1.0).validate()


def test_goal_optional_fields_none():
    """Todos os campos opcionais como None devem ser válidos."""
    goal = make_goal(
        description=None,
        target_date=None,
        current_amount=None,
        priority=None,
        monthly_contribution=None,
        linked_account_id=None,
        assumptions_json=None,
    )
    goal.validate()


# ------------------------------------------------------------------ #
#  Goal.progress_pct()                                                #
# ------------------------------------------------------------------ #

def test_progress_pct_null_when_current_amount_is_none():
    goal = make_goal(current_amount=None)
    assert goal.progress_pct() is None


def test_progress_pct_zero_when_current_amount_is_zero():
    goal = make_goal(target_amount=10000.0, current_amount=0.0)
    assert goal.progress_pct() == 0.0


def test_progress_pct_calculated():
    goal = make_goal(target_amount=10000.0, current_amount=5000.0)
    assert goal.progress_pct() == 50.0


def test_progress_pct_exactly_100():
    goal = make_goal(target_amount=10000.0, current_amount=10000.0)
    assert goal.progress_pct() == 100.0


def test_progress_pct_capped_at_100():
    """Quando current_amount > target_amount, o progresso não deve passar de 100%."""
    goal = make_goal(target_amount=10000.0, current_amount=15000.0)
    assert goal.progress_pct() == 100.0


def test_progress_pct_partial():
    goal = make_goal(target_amount=30000.0, current_amount=12000.0)
    assert abs(goal.progress_pct() - 40.0) < 0.001
