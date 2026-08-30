"""Solve the PDDL 2.1 model with Aries and print the temporal plan.

Run it from the repository root:

    uv run scripts/solve.py

The default output is the plan alone; `--verbose` prefixes it with a header naming the model files
and the engine.

The script itself finds the model from its own location, so only the path in the command above is
relative to where you run it.
"""

import argparse
import sys

from unified_planning.engines import PlanGenerationResultStatus
from unified_planning.engines.results import POSITIVE_OUTCOMES
from unified_planning.shortcuts import OneshotPlanner

from model import (
    PLANNER_NAME,
    TIMEOUT_SECONDS,
    format_header,
    format_plan,
    load_problem,
    silence_credits,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Solve the tutorial model with Aries and print the temporal plan.")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="print a header naming the model files and the engine before the plan",
    )
    args = parser.parse_args()

    silence_credits()

    if args.verbose:
        print(format_header())
        print(flush=True)  # keep this header ahead of anything the parser may write to stderr

    try:
        problem = load_problem()
    except Exception as exc:  # noqa: BLE001 - the PDDL parser raises several unrelated types
        # While editing the model, a parse error is the expected failure, and its message names the
        # offending line. A Python traceback through the parser would only bury it.
        print(f"could not read the model: {exc}", file=sys.stderr)
        return 1

    with OneshotPlanner(name=PLANNER_NAME) as planner:
        result = planner.solve(problem, timeout=TIMEOUT_SECONDS)

    if result.status == PlanGenerationResultStatus.TIMEOUT:
        print(
            f"Aries found no plan within {TIMEOUT_SECONDS}s.\n"
            "For a model this small that almost always means the goal is unreachable: some\n"
            "condition in the domain can never be satisfied. Aries keeps searching instead of\n"
            "reporting that, so a timeout here is a result about the model, not a slow machine.",
            file=sys.stderr,
        )
        return 1

    if result.status not in POSITIVE_OUTCOMES:
        print(f"no plan found ({result.status.name})", file=sys.stderr)
        return 1

    print(f"plan ({len(result.plan.timed_actions)} actions):")
    print(format_plan(result.plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
