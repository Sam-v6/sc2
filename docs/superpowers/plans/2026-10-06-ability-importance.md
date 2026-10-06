# Human-command importance weighting implementation plan

> **For agentic workers:** Use superpowers:executing-plans in the existing
> isolated worktree. Autonomous execution is authorized; no additional approval.

**Goal:** Test failure to choose human production/construction commands under
a teaching distribution dominated by Smart and Attack.

**Architecture:** Opt-in teaching-only weights for full supervised commands.
Keep uniform shuffled traversal, every input/head/action and the unweighted
default. Adapt published weighting to independent command examples, without
claiming to reproduce its recurrent trajectory sampler.

**Tech stack:** NumPy, existing joint Adam trainer, unittest.

**Spec:** `docs/learning-execution.md`,
`logs/roadmap/professional-command-failures-01.json` and
[TStarBot-X section4.4](https://arxiv.org/pdf/2011.13729).

## Global constraints

CPU-only, BLAS/OMP2threads, approximately80%ceiling. No downloads/sudo/native
games/RL. Nine corpus07 teaching games; reused774diagnostic. Reserved
848/51483/51886 excluded. One fixed experiment, no weighting sweep.

## Review focus

Counts/weights use representable teaching commands only, never diagnostics.
Apply identical example weights to every supervised loss/gradient branch.
Preserve default Adam behavior and every human command.
Bound rare-action influence; keep unit/group/target labels unchanged.
Do not describe the changed objective as preserving human action frequency.

## Task 1: Verified weighted supervision

Files: `src/learning/entity_train.py`, `tests/test_entity_importance.py`.

- [x] Observe failing tests for weights/bounds/global mean, unit-weight default
  parity and weighted-batch/duplicated-example equivalence.
- [x] Implement `ability_importance_weights(abilities, replay_count)`:

  ```python
  counts = Counter(abilities)
  weights = np.array([
      .25 if ability == 1 else min(10., max(1., replay_count / counts[ability]))
      for ability in abilities
  ])
  return weights / weights.mean()
  ```

  Ability1 is native Smart; no NOOP teaching commands exist. Cap10 precedes
  global mean normalization. Optional weights in Adam.step multiply every
  example's loss/gradient before batch averaging. Add --ability-importance and
  bind the rule, actual counts and weights in configuration. Derive weights
  after filtering teaching labels. Preserve shuffled order and update count.
- [x] Focused/full unittest, Ruff/diff checks, independent review, commit before
  fitting. No encoder architecture or supervised loss-internal changes.

## Task 2: Fixed human-only experiment

- [x] Freeze fit07 against fit05: identical nine teachers and774,hidden32,
  seed8100,rate.001,batch16,50epochs/14100updates,600optimizer-second cap,
  refinement/actor cutoff/spatial/availability/role pooling/actor-relative points.
  Context normalization false in both; add only ability importance.
- [x] Verify terminal/source/code/checkpoint and matched updates. Report frozen
  unweighted loss separately from the weighted training objective. All diagnostics
  use trainer.collect, and aggregate fields must match trainer reports.
- [x] Evaluate diagnostic gates: at least24/292complete; at least35/91correct abilities
  among Build/Train/Research commands; at least one correct ability for each
  SupplyDepot,Barracks,Marine production (319,321,560); total ability at least
  139/292; Smart/Attack ability at least119/198. Teaching complete at least825.
  These development gates do not establish competence or Hard wins.
- [x] Report per-family actors/targets and natural-frequency copying. No reserved
  predictions/promotion without later frozen functional evidence. Failure ends
  this experiment; success still needs native imitation competence, learned micro
  transfer, reliable all-race Hard and higher-difficulty evaluation.

## Evidence and tradeoff

Exact trainer-input audit: teaching Smart2103/Attack1232 among4510representable
commands (73.95%). Fit06diagnostic ability0/11SupplyDepot,0/4Barracks,0/12Marine;
Smart114/157,Attack25/41. Oracle construction targeting also generalizes poorly:
SupplyDepot gold-cell offset mean0.78tiles teaching versus3.32diagnostic. Unit
selection remains weak. Weighting cannot be assumed to solve all these problems.
Fit06normalization failed; no extension/tuning. The published weighting inspires
this bounded test, not a guarantee of the paper's Zerg results on nine partial
Terran teaching games. All raw labels, including context-dependent Smart, remain.

## Execution record

Task1: Four tests observed RED then GREEN. Review finds one Important vocabulary
counter overwrite before fitting. Added actual tiny-dataset weighted main-path
test; reproduced IndexError with zero unit embedding rows, renamed counter,
observed GREEN. Full322tests pass in9.92seconds; Ruff/diff checks pass. All full
command gradient branches weighted and shuffled indices aligned. No minors.
Final: fixed vocabulary overwrite by main-path regression RED→GREEN; full suite
322/322. Review declines experiment outcome judgment before fitting; acceptance
will be determined by the frozen gates and terminal evidence, not code review.

Task2 launcher `logs/roadmap/run_professional_importance_fit_01.py` freezes the
contract before subprocess launch, checking source hashes/nativeSmart identity
and diagnostic macro denominator91. Fresh output `joint-professional-fit-07/`.

Ruling: preflight sums91macro commands, correcting the manually counted88 before
any contract, optimizer or model result. Preserve the absolute35correct-ability
threshold; use the actual91denominator. Cost if wrong: the benchmark denominator
would be inconsistent with its frozen command set. No training was launched by
the rejected preflight and no checkpoint/output/contract was created.

Terminal result: fit07 completed 50 epochs and 14,100 updates in 331.97 optimizer
seconds / 387.11 total seconds. Teaching complete copying is 892/4,513;
diagnostic complete copying is 11/292, ability 130, actors 53 and target 69.
Macro ability choice is 13/91, Smart/Attack 117/198. Supply Depot ability is 2/11,
but none has correct actors or target; Barracks 0/4 and Marine production 0/12.
Five diagnostic gates fail; only teaching complete copying passes. The frozen
unweighted teaching loss worsens from 4.260686 to 4.750104. Weighted training
loss is a different objective and must not be compared directly to baseline.

`professional-importance-comparison-01.json` verifies matched configuration,
sources, code, checkpoint, updates, teaching-only weight counts and diagnostic
field aggregates. The loss helper checks all 4,510 component sums against the
actual optimizer loss; its teaching totals match the terminal report. The first
comparison-helper attempt stopped on unnamed static catalog entries before any
receipt; using the catalog's optional friendly names fixes that read-only audit.
Training was neither changed nor repeated. No promotion, native games, reserved
predictions or RL. This experiment ends; no weighting sweep follows.
