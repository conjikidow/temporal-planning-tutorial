# Temporal Planning Tutorial

[![License](https://img.shields.io/badge/license-MIT%2FApache--2.0-blue.svg?style=flat)](#license)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![prek](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/j178/prek/master/docs/assets/badge-v0.json)](https://github.com/j178/prek)
[![CI](https://github.com/conjikidow/temporal-planning-tutorial/actions/workflows/ci.yaml/badge.svg)](https://github.com/conjikidow/temporal-planning-tutorial/actions/workflows/ci.yaml)

**English** | [日本語](README.ja.md)

A hands-on tutorial for temporal automated planning.

The subject is a small Earth-observation satellite.
It must image ground targets, process each image on board into a downlinkable product,
and transmit each product to the ground.
Every stage takes time, the satellite carries one camera, one processor, and one transmitter,
and the primary ground station, which the high-rate link needs, is only usable while it is in view.
A temporal planner decides which of these actions to run, in which order, and at which times.

The tutorial is hands-on, and most of the work happens in the model rather than in the code.
You read and edit a PDDL 2.1 model, run a planner on it, read the plan that comes back,
and correct the model when the plan turns out to be one the satellite could never fly.

A temporal planner searches for actions and timings that satisfy the model.
If the model omits a real-world constraint, the planner is free to exploit that omission.

## Layout

- [`models/pddl/domain.pddl`](models/pddl/domain.pddl):
  the PDDL 2.1 domain, with the types, the predicates, and the durative actions.
- [`models/pddl/problem.pddl`](models/pddl/problem.pddl):
  the PDDL 2.1 problem, with the objects, the initial state, and the goal.
- [`scripts/model.py`](scripts/model.py):
  locating and loading the model and formatting the plans it produces, shared by the two scripts below.
- [`scripts/solve.py`](scripts/solve.py): solve the model with Aries and print the temporal plan.
- [`scripts/validate.py`](scripts/validate.py): check a plan against the model it came from.
- [`docs/tutorial.md`](docs/tutorial.md): the tutorial itself, from the first checkpoint to the reference model.

## Requirements

- Python 3.11 or later.
- [uv](https://docs.astral.sh/uv/).
  - `uv sync` installs the dependencies.

## Tools

Three pieces are involved, and they do different jobs.

- **PDDL 2.1**: the modeling language.
  It is what you write and edit: the types, the predicates, the durative actions, and the problem to solve.
- **[Unified Planning](https://github.com/aiplan4eu/unified-planning)**: a Python integration layer.
  It parses the PDDL, hands the problem to an engine, and returns the result.
  It is infrastructure, not the planning language and not the planner.
- **[Aries](https://github.com/plaans/aries)**: the planning engine.
  It is a constraint-based temporal planner, and it is what actually searches for a plan.

What you write is the model, and what you read is the plan.
The other two are what get you from one to the other.

```text
PDDL 2.1 model
      |
      |  Unified Planning (engine: Aries)
      v
Temporal plan
```

## Tutorial

The tutorial itself is in [`docs/tutorial.md`](docs/tutorial.md).
It starts from a tagged checkpoint rather than from `main`, which already holds the reference model.

> [!CAUTION]
> Every section below this one describes the reference model,
> and gives away the answers to steps 2 and 3.
> If you are going to work through the tutorial, come back to them afterwards.

## Scenario

The domain is named `orbiter`.
It has one type, `target`, and the problem declares two objects of it, `target-a` and `target-b`.

The satellite carries exactly one camera, one processor, and one transmitter.
Each is modeled as a single predicate, `(camera-free)`, `(processor-free)`, and `(transmitter-free)`.
How faithfully the model uses them is the subject of the tutorial.

Mission progress is recorded by one fact per target: `(imaged ?t)`, `(processed ?t)`, and `(downlinked ?t)`.
The goal is that both targets are downlinked.

One predicate describes the environment rather than the satellite.
`(primary-visible)` means the primary ground station is in view.
Orbital geometry controls it, so no action ever claims or releases it.
It appears only in the reference model.

The reference model has four durative actions.

| Action | Duration | Meaning |
| --- | --- | --- |
| `observe ?t` | 5 | image a target; claims the camera |
| `process ?t` | 2 | turn a raw image into a product; claims the processor |
| `downlink ?t` | 3 | high-rate transmission; needs `(primary-visible)` throughout; claims the transmitter |
| `downlink-backup ?t` | 9 | low-rate link, always reachable; claims the transmitter |

Durations are in abstract time units, not seconds.

## Running the planner

```bash
uv run scripts/solve.py
```

```text
plan (6 actions):
0.000: observe(target-a) [5.000]
5.100: observe(target-b) [5.000]
10.100: process(target-a) [2.000]
12.200: process(target-b) [2.000]
14.200: downlink(target-a) [3.000]
17.300: downlink(target-b) [3.000]
```

Each line reads `start: action(arguments) [duration]`, with the times in the model's abstract time units.

Both scripts also take `--verbose`, which prefixes the run with a header naming the model files and the engine.
On `validate.py` it also adds a note on what a `VALID` verdict does and does not mean.

Aries is a satisficing planner.
It returns the first plan it finds rather than the shortest or the fastest one,
and this tutorial sets no optimization metric.

Plans also vary between runs.
Aries is not deterministic run to run,
so the exact start times and the order in which the two targets are handled can differ.
In the reference model both links are legal while the ground station is in view,
and the model states no preference between them, so even the downlink action chosen can differ from the one above.
A run may even serialize actions that the model would allow to overlap.
What is stable is what the model permits and forbids,
and every lesson in the tutorial rests on that rather than on any one schedule.
Output that differs from what is documented here is expected.

The gaps in the plan above separate two happenings that interfere:
PDDL 2.1 forbids one action releasing a resource and another claiming it at the same instant,
and the size of the gap is the planner's choice.
That is why `process(target-b)` starts at 12.200 rather than at 12.100,
where `process(target-a)` releases the processor.

A goal that nothing can reach makes Aries search until it is stopped, rather than report the goal unreachable.
`scripts/solve.py` therefore passes a 30-second timeout,
and reports a timeout as what it almost always means for a model this small:
the goal is unreachable because some condition can never be satisfied.

## Validating a plan

```bash
uv run scripts/validate.py
```

The script solves the current model and then checks the resulting plan against that same model,
using Unified Planning's `up_time_triggered_validator` engine.
The engine is selected by name, so the result does not depend on which other engines happen to be installed.

Two questions are easy to confuse, and only one of them is being answered here.

- Does the plan satisfy the formal model?
  This is what the validator checks, and all it can check.
- Does the model correctly represent the intended real-world constraints?
  This is an engineering judgment, and no validator can make it.

A plan that exploits a constraint the model forgot to state is reported `VALID`.
The tutorial makes deliberate use of exactly that.

## Model behavior

Each target passes through a three-stage pipeline: `observe`, then `process`, then a downlink.
The stages are chained through the mission facts.
`observe` produces `(imaged ?t)`, which `process` requires;
`process` produces `(processed ?t)`, which either downlink action requires;
the downlink produces `(downlinked ?t)`, which the goal requires.
A stage can therefore never run before the stage that feeds it.

In the reference model, every device is claimed at the start of an action and released at its end.
An action deletes the device's free predicate at start and adds it back at end,
so two actions needing the same device cannot overlap in time.
Actions needing different devices are under no such constraint and are free to run concurrently.
So a plan is free to process one target while the camera is already imaging the next,
though a satisficing planner will not always take that option.

`(primary-visible)` is different in kind.
It is a condition the environment controls, not a resource an action claims,
which is why `downlink` states it as an `over all` condition with no matching effects.
The action requires the primary station to be in view for its whole duration, and does nothing to bring that about.
`downlink-backup` needs no primary station at all and takes three times as long,
so the two links are a trade-off rather than a preference.

## License

Licensed under either of [MIT license](LICENSE-MIT) or [Apache License, Version 2.0](LICENSE-APACHE) at your option.

Unless you explicitly state otherwise,
any contribution intentionally submitted for inclusion in this software by you, as defined in the Apache-2.0 license,
shall be dual licensed as above, without any additional terms or conditions.
