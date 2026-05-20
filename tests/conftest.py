import pytest


@pytest.fixture
def tmp_plan_dir(tmp_path):
    plans = tmp_path / ".plans" / "test-plan"
    plans.mkdir(parents=True)
    return plans
