# One-decision macro exploration pilot

**Goal:** Discover whether a single alternative macro choice can improve real
game outcomes when followed by the retained learned greedy policy.

**Reason:** The parent wins 22/30 greedy Medium cases while full stochastic
continuations collect mostly defeats. Previous near-greedy collection still
changed many decisions per game. The completed credit-estimator audit does not
identify a qualifying fix. Astra proposes isolating exploration instead of
assigning another broad trajectory's losses to all of its early choices.

## Fixed design before execution

Use the retained spatial kills-only parent, SHA256
0f3e05d9efd5eba4fd238a6282e462599ffc675f008b98fd42925e99f6bb16c6,
with its original 5,460 features, 27 actions, reward, gamma, primitives and
one-second macro cadence. No source migration, learning or checkpoint writes.

Eight fresh Medium cases, each with a 1,200-second game limit and 180-second
per-game wall limit:

| Seed | Race | Build | Map |
| --- | --- | --- | --- |
| 92000 | Terran | Rush | Simple64 |
| 92001 | Protoss | Timing | TritonLE |
| 92002 | Zerg | Power | Simple64 |
| 92003 | Terran | Macro | TritonLE |
| 92004 | Protoss | Air | Simple64 |
| 92005 | Zerg | Rush | TritonLE |
| 92006 | Terran | Timing | Simple64 |
| 92007 | Protoss | Power | TritonLE |

Run one unchanged greedy parent game per case. With NumPy default_rng seeded
420000+case_seed, draw one uniform time in [0,300). Select the first recorded
decision at or after that time with at least two legal actions. Exclude the
parent action and uniformly choose up to two distinct alternatives without
replacement using that same RNG. This rule cannot depend on outcome or return.
If no eligible decision exists, retain the case as unavailable; do not resample.

For each alternative, restart the same seeded case, follow the parent normally,
inject exactly that one legal action at the selected decision index, then resume
the parent. Require exact observations, masks and parent choices through the
intervention state. Prefix mismatch makes that pair unusable; preserve it and
close the pilot if reproducibility fails. The intervention action must execute
under the existing constraints. Record nonexecution as inconclusive, not a valid
alternative discovery. No scripted worker quota, build order or unit mix.

Audit full recorded choices, reward components, discounted returns, replay
receipts, source hashes and checkpoint immutability. Report paired return
differences and outcome transitions separately. Repeated exploration choices
must never enter a PPO rollout buffer.

## Predeclared mechanism gate and stop

At least two executed alternatives from different cases must improve discounted
return without changing a parent victory into a non-victory. At least one
alternative must change a parent non-victory into a victory. Otherwise close
without fitting or extension. Maximum eight parent plus sixteen branch games;
no repeats to repair outcomes. Failure is evidence about this narrow exploration
design, not proof that single-step decisions can never help.

Only a fully audited pass permits separately predeclared reward-driven policy
improvement: freeze representation, update only the state-conditioned output
head using paired rewards, anchor behavior to a fixed parent bank, use fresh
optimizer state and no critic. That fit and a separate matched 12-case Medium
comparison require their own concrete settings, change bound and review before
execution. No pilot result establishes reliable Hard strength or promotion.

## Implementation checks and limits

- [x] Freeze an isolated copy of current main runtime and diagnostic driver.
- [x] Test exactly-one override, legal-action enforcement, identical intervention
  state/mask, unchanged greedy continuation, and unavailable-case handling.
- [x] Confirm the seed bank is unused, freeze cases/RNG rule/input/source hashes,
  then run and audit the bounded pilot.
- [x] Independently review gate results before any conditional fit.

Artifacts go under ignored `logs/one-decision-exploration/`. At most four total
SC2 engines, existing low_load eight-CPU affinity/nice10, CPU learner, single
BLAS thread, no sudo/downloads. Sample active total host CPU against the user's
below-40% preference. Main policy remains unchanged throughout the pilot.

## Initial core preflight

The isolated `source/intervention.py` implements outcome-independent selection
and a policy wrapper that asserts the recorded prefix, injects one different legal
action, then delegates all later choices to the parent. Six focused tests pass
after the initial missing-module failures. No SC2 games or optimizer steps have
been run for this pilot. The declared seed bank was not found in scanned prior
audit JSON/input manifests; the search scope is recorded in `seed-bank-check.json`.
Runtime archive, worker driver, input freeze and full game audit are still required.
Independent core review passes and reproduces selection for all eight seeds.
`logs/audit/one-decision-core-review.json` identifies the remaining runtime checks:
override firing and execution, raw-prefix equality, no rollout/checkpoint writes,
and preserved failures within the declared game/concurrency budget.

## Completed pilot: discovery gate passed

The frozen runtime, driver and audit pass 13 focused tests and independent review.
Review found and verified fixes for interruption receipt retention and truncated
selection coverage before any games. The 40-file input/source freeze is recorded
in `logs/one-decision-exploration/inputs.json`.

All eight parent games and nine selected branches completed without failures;
states with only one alternative required fewer than the maximum 24 games.
Parents won four and lost four. The full audit verifies all 9,390 decisions,
greedy choices except the one injection, exact raw prefixes, reward components,
finite return telescoping, replays and immutable parent/source hashes.
Independent review confirms all checks and both discovery gates.

| Seed | Injected alternative | Parent → branch | Return difference |
| --- | --- | --- | ---: |
| 92000 | wait instead of SCV | Defeat → Victory | +.594201 |
| 92001 | wait instead of retreat | Defeat → Defeat | +.027025 |
| 92002 | Engineering Bay instead of wait | Victory → Victory | -.005007 |
| 92003 | attack instead of wait | Defeat → Victory | +.736167 |
| 92004 | Engineering Bay instead of retreat | Victory → Victory | -.025755 |
| 92004 | wait instead of retreat | Victory → Victory | -.000400 |
| 92005 | wait instead of retreat | Victory → Victory | -.031030 |
| 92006 | Engineering Bay instead of wait | Victory → Defeat | -.574205 |
| 92007 | wait instead of refinery | Defeat → Victory | +.586318 |

Four distinct cases improve return without losing a parent victory, including
three loss-to-win transitions spanning Terran and Protoss. The harmful 92006 branch
is retained and excluded from the improvement count. These are reward discoveries
under a competent continuation, not a generally improved policy or a prescribed
worker/build/attack rule. Conditional policy fitting still requires its own
reviewed objective, behavior bounds and fresh matched evaluation.

Active host samples measured 11.027–13.723% total CPU, owned roughly 9.3–12.4%.
All owned processes used CPUs 24–31/nice10. GPU measured 13%/19.82W/40C; this
pilot performs no GPU learning. Evidence: `logs/audit/one-decision-resource-load.json`.

Complete evidence: `logs/one-decision-exploration/{summary,ledger,selections,pairs,audit}.json`
and `logs/audit/one-decision-complete-independent-review.json`. No model fitting,
PPO rollout collection, optimizer updates or checkpoint writes occurred.

The 92003 attack branch's actual winning replay exports to
`logs/replay-proof/one-decision-terran-macro-win.mp4`: 460 H264 frames at 960x720,
4fps, 115 video seconds, full 450.71 game seconds, no frame cap. ffprobe and an
85-second still verify rendered game content. Overview is omniscient for viewing;
the policy still uses fog-limited observations. The initial incorrect map-directory
path fails before rendering and is preserved separately; the successful export
uses the manifest's installed Ladder2019Season3/TritonLE map.

The [conditional head-fit plan](2026-10-05-paired-head-policy-improvement.md) now
fixes the learned objective, fresh optimizer, behavior-change limits, frozen-only
artifact contract and separate matched game gate. Independent design review passes;
implementation and actual fitting remain the next work.
