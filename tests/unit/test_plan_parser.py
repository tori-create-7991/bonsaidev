"""Tests for plan.md parser."""

import textwrap

from bonsai.state.plan import parse_plan, set_plan_status, update_task_status

SAMPLE_PLAN = textwrap.dedent("""\
    # Test Plan

    ## Some section
    - [x] A1: first task
    - [ ] A2: second task
    - [x] A3: third task
    - [ ] A4: fourth task

    ## Status: running
""")

PLAN_WITH_NEEDS_INPUT = textwrap.dedent("""\
    # Test Plan

    - [ ] B1: only task

    ## Status: needs_input
    ## Pending Question: Should I use foo or bar?
    ## Question Context: Context here.
""")


def test_parse_plan_basic(tmp_path):
    plan_file = tmp_path / "plan.md"
    plan_file.write_text(SAMPLE_PLAN)

    state = parse_plan(plan_file)

    assert state.plan_name == plan_file.parent.name
    assert len(state.tasks) == 4
    assert state.tasks[0].done is True
    assert state.tasks[1].done is False
    assert state.tasks[2].done is True
    assert state.tasks[3].done is False


def test_parse_plan_status(tmp_path):
    plan_file = tmp_path / "plan.md"
    plan_file.write_text(SAMPLE_PLAN)
    state = parse_plan(plan_file)
    assert state.status == "running"


def test_parse_plan_completed_tasks(tmp_path):
    plan_file = tmp_path / "plan.md"
    plan_file.write_text(SAMPLE_PLAN)
    state = parse_plan(plan_file)
    assert state.completed_tasks == 2
    assert state.total_tasks == 4


def test_parse_plan_needs_input(tmp_path):
    plan_file = tmp_path / "plan.md"
    plan_file.write_text(PLAN_WITH_NEEDS_INPUT)
    state = parse_plan(plan_file)
    assert state.status == "needs_input"
    assert state.pending_question == "Should I use foo or bar?"
    assert state.question_context == "Context here."


def test_parse_plan_missing_status(tmp_path):
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("# Plan\n- [ ] X: task\n")
    state = parse_plan(plan_file)
    assert state.status is None


def test_update_task_status(tmp_path):
    plan_file = tmp_path / "plan.md"
    plan_file.write_text(SAMPLE_PLAN)

    update_task_status(plan_file, task_index=1, done=True)

    state = parse_plan(plan_file)
    assert state.tasks[1].done is True


def test_set_plan_status_completed(tmp_path):
    plan_file = tmp_path / "plan.md"
    plan_file.write_text(SAMPLE_PLAN)

    set_plan_status(plan_file, "completed")

    state = parse_plan(plan_file)
    assert state.status == "completed"


def test_set_plan_status_needs_input(tmp_path):
    plan_file = tmp_path / "plan.md"
    plan_file.write_text(SAMPLE_PLAN)

    set_plan_status(
        plan_file,
        "needs_input",
        pending_question="Which approach?",
        question_context="Need to decide.",
    )

    state = parse_plan(plan_file)
    assert state.status == "needs_input"
    assert state.pending_question == "Which approach?"
