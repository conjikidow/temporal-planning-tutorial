"""Locate and load the tutorial model, and format the plans it produces.

`solve.py` and `validate.py` both start from here, so the knowledge of where the model lives and
how a temporal plan is printed is kept in one place.

The model is a PDDL 2.1 domain and problem under `models/pddl/`.
"""

from pathlib import Path

from unified_planning.io import PDDLReader
from unified_planning.model import Problem
from unified_planning.plans import TimeTriggeredPlan
from unified_planning.shortcuts import get_environment

# `scripts/` sits directly under the repository root, so the root is one level up from this file.
# Resolving `__file__` first means the scripts work from any working directory.
REPO_ROOT = Path(__file__).resolve().parents[1]

PDDL_DIR = REPO_ROOT / "models" / "pddl"
DOMAIN_FILE = PDDL_DIR / "domain.pddl"
PROBLEM_FILE = PDDL_DIR / "problem.pddl"

# Aries is the planning engine. Unified Planning only parses the model and hands it over.
PLANNER_NAME = "aries"

# Aries searches until it finds a plan, so a goal that nothing can reach makes it run forever rather
# than report that the goal is unreachable. Every model in this tutorial is solved in well under a
# second, so hitting this limit is a statement about the model, not about the machine.
TIMEOUT_SECONDS = 30


def load_problem() -> Problem:
    """Parse the PDDL 2.1 domain and problem into a Unified Planning problem."""
    for path in (DOMAIN_FILE, PROBLEM_FILE):
        if not path.is_file():
            msg = f"model file not found: {path.relative_to(REPO_ROOT)}"
            raise FileNotFoundError(msg)

    return PDDLReader().parse_problem(str(DOMAIN_FILE), str(PROBLEM_FILE))


def silence_credits() -> None:
    """Stop Unified Planning from printing an engine credits banner before every run.

    The banner is useful in general, but here it would bury the plan under a block of text that
    never changes. Aries is credited in the README instead.
    """
    get_environment().credits_stream = None


def format_header() -> str:
    """Render the header naming the model files and the planning engine.

    Both scripts keep it behind `--verbose`. What changes while a model is being edited is the plan
    and the verdict, so that is what the default output shows.
    """
    return (
        f"domain:  {DOMAIN_FILE.relative_to(REPO_ROOT)}\n"
        f"problem: {PROBLEM_FILE.relative_to(REPO_ROOT)}\n"
        f"planner: {PLANNER_NAME}"
    )


def format_plan(plan: TimeTriggeredPlan) -> str:
    """Render a temporal plan as one `start: action [duration]` line per action.

    Actions are sorted by start time, then by their printed form, so that two runs that find the
    same plan print it identically.
    """
    lines = []
    for start, action, duration in sorted(plan.timed_actions, key=lambda item: (item[0], str(item[1]))):
        # Timestamps come back as exact rationals; render them as fixed-point decimals. Only
        # durative actions carry a duration, so an instantaneous one would print without a suffix.
        suffix = "" if duration is None else f" [{float(duration):.3f}]"
        lines.append(f"{float(start):.3f}: {action}{suffix}")
    return "\n".join(lines)
