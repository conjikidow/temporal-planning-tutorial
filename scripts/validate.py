"""Check a plan produced by Aries against the PDDL 2.1 model it came from.

Run it from the repository root:

    uv run scripts/validate.py

The default output is the plan and the verdict; `--verbose` prefixes the run with a header naming
the model files and the engine, and adds a note on what a VALID verdict does and does not mean.

What this checks is narrow, and the narrowness is the point. The validator replays the plan against
the model: it confirms that every condition holds when the model requires it to hold, and that the
goal holds at the end. So it answers "does this plan satisfy the model?" and nothing else.

It cannot answer "does the model say what I meant?", because the model is its only source of truth.
A plan that exploits a constraint the model forgot to state is therefore reported as VALID.

The script solves the model afresh rather than reusing an earlier run. Aries is not deterministic,
so the plan checked here may differ from the one `solve.py` last printed; it is printed too, so that
what was checked is always visible.
"""

import argparse
import sys

from unified_planning.engines import PlanGenerationResultStatus, ValidationResultStatus
from unified_planning.engines.results import POSITIVE_OUTCOMES
from unified_planning.shortcuts import OneshotPlanner, PlanValidator

from model import PLANNER_NAME, TIMEOUT_SECONDS, format_header, format_plan, load_problem, silence_credits

# Selected by name rather than by problem kind, so that the answer does not depend on which other
# engines happen to be installed. This one handles the time-triggered plans Aries returns.
VALIDATOR_NAME = "up_time_triggered_validator"


def main() -> int:
    parser = argparse.ArgumentParser(description="Solve the tutorial model and check the plan against it.")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="print a header naming the model files and the engine, and a note on what VALID means",
    )
    args = parser.parse_args()

    silence_credits()

    if args.verbose:
        print(format_header())
        print(flush=True)  # keep this header ahead of anything the parser may write to stderr

    try:
        problem = load_problem()
    except Exception as exc:  # noqa: BLE001 - the PDDL parser raises several unrelated types
        print(f"could not read the model: {exc}", file=sys.stderr)
        return 1

    with OneshotPlanner(name=PLANNER_NAME) as planner:
        result = planner.solve(problem, timeout=TIMEOUT_SECONDS)

    if result.status not in POSITIVE_OUTCOMES:
        if result.status == PlanGenerationResultStatus.TIMEOUT:
            print("no plan to validate (TIMEOUT): the goal is most likely unreachable", file=sys.stderr)
        else:
            print(f"no plan to validate ({result.status.name})", file=sys.stderr)
        return 1

    print("plan:")
    print(format_plan(result.plan))
    print()

    with PlanValidator(name=VALIDATOR_NAME) as validator:
        validation = validator.validate(problem, result.plan)

    print(f"validator: {VALIDATOR_NAME}")
    print(f"result:    {validation.status.name}")

    if validation.status != ValidationResultStatus.VALID:
        # Aries produced this plan from this very model, so an INVALID verdict means the planner and
        # the validator disagree about the model. That is a tool problem, not a broken PDDL edit.
        if validation.reason is not None:
            print(f"reason: {validation.reason.name}", file=sys.stderr)
        if validation.inapplicable_action is not None:
            print(f"inapplicable action: {validation.inapplicable_action}", file=sys.stderr)
        return 1

    if args.verbose:
        print()
        print("VALID means the plan satisfies the model.")
        print("Whether the model states every constraint that holds in reality is a separate question,")
        print("and not one a validator can answer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
