# Tutorial

**English** | [日本語](tutorial.ja.md)

You read a small temporal model, complete it, watch the planner return a plan that could never be flown,
and fix what the model failed to say.

The tools you need, and the one command that installs them, are in the README's
[Requirements](../README.md#requirements) section.
If you read on there, stop before [Scenario](../README.md#scenario):
everything from that section down describes the reference model and gives away steps 2 and 3.

## Where to start

Clone the repository:

```bash
git clone https://github.com/conjikidow/temporal-planning-tutorial.git
cd temporal-planning-tutorial
uv sync
```

`main` holds the reference model, so starting there would spoil it.
Start from the first checkpoint instead, on a branch of your own:

```bash
git switch -c tutorial-work step-0
```

All four steps are done on that one branch, by editing the files under [`models/pddl/`](../models/pddl/) in place.
Each step opens by taking its starting files from a tag, and the same tags let you start a step over if you get stuck.
See [Checkpoints](#checkpoints).

## Step 0: read the model and run it

Read the two files in this order.

- [`models/pddl/domain.pddl`](../models/pddl/domain.pddl) is the **domain**.
  It says what kinds of things exist, what facts can be true of them, and what actions the satellite can perform.
  It describes a machine, not a mission, and it is the same on every day of the mission.
- [`models/pddl/problem.pddl`](../models/pddl/problem.pddl) is the **problem**.
  It says which objects exist today, which facts are true at the start, and which facts must be true at the end.
  It is one concrete request against that machine.
  Note that the catalog declares two targets while the goal names only one; an object may exist without being asked for.

The domain has two actions so far, and both are `:durative-action`,
meaning they occupy an interval of time rather than an instant.
Read `process` closely, because everything you write later imitates it:

```lisp
(:durative-action process
  :parameters (?t - target)
  :duration (= ?duration 2)
  :condition (and
    (at start (processor-free))
    (over all (imaged ?t))
  )
  :effect (and
    (at start (not (processor-free)))
    (at end (processor-free))
    (at end (processed ?t))
  )
)
```

Three temporal qualifiers appear in PDDL 2.1, and each says *when* a condition is tested or an effect applied.

- `at start` — at the instant the action begins.
- `at end` — at the instant it finishes.
- `over all` — throughout the interval between the two.
  - The condition has to hold without a break for that whole interval.

So `process` tests that the processor is free at the instant it starts,
holds the raw image for its whole duration, and marks the product finished at the end.
The pair of effects on `(processor-free)` is worth naming now:
the action **claims** the processor at start and **releases** it at end.
That is how one physical device is modeled in PDDL 2.1.

Now run the planner:

```bash
uv run scripts/solve.py
```

```text
plan (2 actions):
0.000: observe(target-a) [5.000]
5.000: process(target-a) [2.000]
```

Each line reads `start: action(arguments) [duration]`, in the model's abstract time units.

> [!NOTE]
> Run it again and you may get a different plan.
> Aries, the engine searching here, returns the first plan it finds rather than the shortest one,
> and it is not deterministic between runs.
> Your timestamps may differ from the ones printed here, the two targets may be handled in the other order,
> and actions the model allows to overlap may come back serialized.
> Every lesson below rests on what the model permits and forbids, never on the exact plan you happen to get.

This is what a planner does.
Nobody told it to observe before processing, and nobody told it to start processing at 5.
It was given an initial state and a goal,
and it searched for a set of actions *and start times* such that every condition holds when the model requires it,
and the goal holds at the end.
`process` could not start earlier because it needs `(imaged target-a)`, which only exists once `observe` has finished.
The ordering is a consequence of the conditions, not an instruction.

**Lesson:** A domain describes possibilities, a problem describes one request,
and a planner searches for actions and timings that satisfy both.

## Step 1: complete a durative action

The satellite can image and process, but nothing yet reaches the ground.
Bring in the third action:

```bash
git restore --source=step-1 -- models/pddl/
```

That adds the `(downlinked ?t)` and `(transmitter-free)` predicates, sets the transmitter free in the initial state,
changes the goal to `(downlinked target-a)`, and appends a `downlink` action that is not finished.

In this step you only edit [`models/pddl/domain.pddl`](../models/pddl/domain.pddl).
Everything left to you is marked with a `TODO`, and there are three of them:

```bash
grep -n TODO models/pddl/domain.pddl
```

You supply the duration, the conditions, and the effects.
The comments state what the action must do in real-world terms; `process` shows every form you need.
The placeholders are not valid PDDL, so the model does not parse until you replace them.
That makes the parser your worklist:

```bash
uv run scripts/solve.py
```

```text
could not read the model: Found invalid expression: todo-duration. From line: 51, col 28 to line: 51, col 41
```

It reports one at a time, with a line and column.
Fill that one in, run again, and it points at the next.

The step is over when the planner returns a three-action plan that images, processes, then downlinks `target-a`:

```text
plan (3 actions):
0.000: observe(target-a) [5.000]
5.000: process(target-a) [2.000]
7.000: downlink(target-a) [3.000]
```

Check the plan rather than just the absence of an error.
A one-action plan that downlinks at `0.000` is a passing parse and a failed model:
it means your conditions never required the product to exist,
so the planner transmits data the satellite has not acquired.

**Lesson:** A durative action is a duration, a set of conditions tagged by when they are tested,
and a set of effects tagged by when they are applied.
Precedence between actions is not stated anywhere; it emerges from one action needing what another produces.

## Step 2: the plan that cannot be flown

This is the important step.

Operations wants both targets in the same pass.
Take the extended goal:

```bash
git restore --source=step-2 -- models/pddl/problem.pddl
```

If your step 1 is unfinished, or if the planner times out below,
take the whole directory instead with `git restore --source=step-2 -- models/pddl/`.
A `downlink` that claims the transmitter without releasing it at end survives step 1,
where one transmission is enough, and only becomes unsolvable now that a second one has to follow it.

If the plan comes back without two observations at the same instant, run it again rather than restoring:
Aries is free to serialize actions the model merely permits to overlap, and restoring hands back the same domain.
What the step rests on is that the model does not *forbid* that overlap, not that any one run exhibits it.

Only the goal changed.
The domain is exactly as you left it, so nothing about the satellite's physics has changed — only the request.
Run it:

```bash
uv run scripts/solve.py
```

```text
plan (6 actions):
0.000: observe(target-a) [5.000]
0.000: observe(target-b) [5.000]
5.000: process(target-a) [2.000]
7.100: process(target-b) [2.000]
9.100: downlink(target-a) [3.000]
12.200: downlink(target-b) [3.000]
```

Look at the first two lines.
The satellite has one camera, and the plan images two different targets with it at the same instant.
That plan cannot be flown.

Before you change anything, check a plan of that shape against the model:

```bash
uv run scripts/validate.py
```

The script solves the model again before validating, so the plan it prints is not always the one you just read.
The verdict is what matters here, and it reads:

```text
result:    VALID
```

The validator agrees with the planner.
Both are correct, and the plan really does satisfy the model — which means the model is what is wrong.

Now find out why.
The evidence you need is already in the plan you just read.
Two `process` actions appear, and they do **not** overlap: the second waits for the first to finish.
Two `downlink` actions appear, and they do not overlap either.
Only the camera failed to keep its two users apart.

Fix the model, then run the planner again.
The step is over once the two observations come back separated.

When they do, the second one will start slightly after the first ends rather than at the same instant.
That gap is not rounding.
PDDL 2.1 forbids two interfering happenings at the same instant,
and one action releasing the camera while another tests for it is exactly such a pair, so they must be separated.

Note also that the corrected model still permits concurrency.
Actions using different devices may overlap, so a plan that runs `process` or `downlink`
while `observe` is still in progress is perfectly legal.
Your run may serialize everything instead, because Aries stops at the first schedule it finds,
but nothing in the model forbids those overlaps.
Concurrency was never the bug.
The corrected model forbids exactly the overlap that was impossible and permits the rest.

**Lesson:** The planner is not wrong. The model was incomplete.
A condition constrains when an action may run; only effects change the world.
Requiring a fact that is true from the start and that nothing ever falsifies rules nothing out.
A planner searches the model you gave it, and it will exploit anything you failed to say.

## Step 3: planning, not just scheduling

So far every action in every plan was forced.
There was exactly one way to make `(downlinked ?t)` true, so the planner's only real decisions were ordering and timing.
That is scheduling.
Give it something to decide.

Unlike the restores that opened steps 1 and 2, this one is optional; take it only if you want the corrected model:

```bash
git restore --source=step-3 -- models/pddl/
```

The high-rate link only works while the primary ground station is in view,
and there is a slower backup link that is always reachable.
Make three changes; the first of them touches both files.

1. Add a `(primary-visible)` predicate to the domain, and add `(primary-visible)` to the initial state in the problem.
2. Require the primary station to be in view for the whole of `downlink`,
   since losing the station mid-pass would break the transmission.
3. Add a `downlink-backup` action: the same conditions and effects as `downlink`,
   except that it does not need the primary station and it takes 9 time units instead of 3.
   Both links share the one transmitter.

Note what `(primary-visible)` is and is not.
It is a fact about the world that the satellite does not control, so no action claims or releases it.
It gets an `over all` condition and no effects at all — which is the correct use of `over all`,
and precisely what `(camera-free)` was not.

Run the planner.
The goal now has two producers, so the planner must choose one; either link is legal, for the reason given below.

Then run the experiment.
Delete `(primary-visible)` from the initial state in [`models/pddl/problem.pddl`](../models/pddl/problem.pddl),
and run again.
Deleting the fact is all it takes to make it false: anything absent from `:init` is false, not unknown.
The downlink lines of the plan now name the backup link:

```text
...: downlink-backup(target-a) [9.000]
...: downlink-backup(target-b) [9.000]
```

Run it a few times, and read the action names rather than the times.
Every run names `downlink-backup`, and that is the stable part:
with the station out of view the fast link is not merely worse, it is unusable,
so the planner selects the only action that can produce the goal.

With the station visible, the evidence is weaker, so run it a few times there too.
Both actions are legal then, and the model says nothing about preferring the fast one,
so Aries is free to return either — it stops at the first plan it finds.
It may well return the same one every time; that is the search settling, not the model choosing.
If you want the shorter link preferred, that preference has to be written into the model;
it is not something the planner owes you.
This is step 2's lesson from the other side: the planner does exactly what the model says, no more.

Put `(primary-visible)` back, and compare your work with the reference model:

```bash
git diff main -- models/pddl/
```

Expect that diff to be mostly comments:
`main` carries explanatory ones you had no reason to write, and your resolved `TODO` blocks are probably still there.
What to read are the conditions and the effects; if those agree, your model says what the reference model says,
and a diff of nothing but comments is the expected outcome.

**Lesson:** A temporal planner decides three different things, and you have now seen each on its own:

- **which** actions to use — `downlink` or `downlink-backup`;
- **in what order** — `process` before `downlink`, forced by the conditions;
  one target before the other on each shared device, the serialization forced by the claims;
- **at what times** — start times consistent with durations, device claims, and the separation PDDL 2.1 requires.

From here, two directions are worth taking.
Add a third target and work out which parts of the plan the model forces to serialize.
Or give the satellite a second camera,
and work out what has to change in the model before the planner is allowed to use it.

## Checkpoints

Each tag holds the state the corresponding step starts from.

| Tag | State |
| --- | --- |
| `step-0` | `observe` and `process`, with a single-target goal. |
| `step-1` | The same, plus a `downlink` action left incomplete with `TODO` markers. |
| `step-2` | The same, with `downlink` completed and the goal extended to both targets. |
| `step-3` | The same, with the camera modeled correctly. |
| `main` | The same, plus the choice between the high-rate and the backup link. |

The answer to a step is therefore the tag of the step after it.
To skip a step, or to recover a working tree you would rather forget, take those files back:

```bash
git restore --source=step-2 -- models/pddl/    # skip step 1
git restore --source=step-3 -- models/pddl/    # skip step 2
git restore --source=main -- models/pddl/      # skip step 3
```

To compare your work with the reference model at any point:

```bash
git diff main -- models/pddl/
```
