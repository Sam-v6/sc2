# Resource collection learning results

The separately declared collection objective passed its physical accounting
fixture, all 32 training games and independent complete-data review. The final
policy then passed the frozen auxiliary comparison: mean collection rose from
5,258.875 to 5,814.25 resources, a gain of 555.375 (10.56%). All eight matched
cases improved. This is learned economic behavior, not established Hard strength.

## Recorded training

The original launch failed before any game because spawned children resolved an
older generic worker module. Its immutable source, failed receipts and zero-game
audit remain retained. The separately reviewed
[spawn repair](2026-10-05-collection-runtime-spawn-repair.md) used unique module
names and a real spawned-process regression; it reused only proved unplayed cases.

The corrected run completed exactly 32 ordinary 300-second VeryEasy games in
eight four-game batches. All games reached their declared time limit. There were
8,992 decisions and 160 PPO optimizer steps, with no failed or replaced games.
The final checkpoint equals the last batch checkpoint; no earlier model was
selected. Training mean collection was 5,101.25 resources. The nearly flat
sampled training curve did not predict the later greedy comparison's improvement.

Independent review reconstructed every sampled choice, terminal collection
reward, likelihood and Monte Carlo return; verified merged learner inputs,
optimizer ages, moments and RNG chain; reconciled 17,984 journal events; checked
all replays and bound 209 training artifacts by SHA-256. It did not rerun optimizer
updates. Collection endpoints use the last prepared BotAI score observation.

## Frozen auxiliary comparison

Both unchanged initial actor and final actor faced the eight predeclared cases
111000–111007, covering all races, both maps and all five computer builds. All
16 games and 4,496 greedy decisions passed independent review, with unchanged
checkpoint bytes, no optimizer steps and no collected training rollout.

| Opponent race | Mean paired collection gain |
| --- | ---: |
| Terran | 516.33 |
| Protoss | 571.67 |
| Zerg | 589.50 |

The threshold was 262.94375 resources: the larger of 100 resources and 5% of
parent mean collection. The candidate exceeded it, with positive gains in all
three races. All eight cases improved, by 436–635 resources.

The candidate finished with 37–41 workers and 2–4 bases. It had zero logged army
supply throughout every evaluation game. This objective rewarded harvesting;
it did not reward wealth, surviving assets, combat or victory. Economic success
therefore requires the separate full-game transfer test before further work.

## Full-game transfer and resource use

The separately reviewed, frozen 24-game Hard transfer completed all original
12 cases 112000–112011 without failures. Both actors used ordinary combat scoring
and the retained parent discount through an inference-only adapter.

| Policy | Hard wins / 12 | Mean discounted combat return |
| --- | ---: | ---: |
| Retained parent | 5 | 0.268225 |
| Collection candidate | 0 | -0.080000 |

The parent won twice against Terran, once against Protoss and twice against Zerg.
The candidate lost all 12 games and had zero logged army supply throughout every
game. All five parent victories became candidate defeats; no parent defeat became
a candidate victory. Mean paired return fell by 0.348225. Every transfer gate
failed: additional wins were -5 rather than at least +2; mean return fell; win
gains were negative for all three races. Independent review verified all 14,153
decisions, greedy choices, ordinary rewards and discounted telescopes, journals,
replays and unchanged checkpoints; it bound 471 artifacts including inherited
evidence. There were no evaluation optimizer steps or training rollouts.

This arm is closed without fitting against validation, replacement, extension
or promotion. The economic task demonstrably changed macro behavior, but its
harvesting objective did not preserve fighting capability. Any subsequent
economic/combat training must be a separately declared experiment. The retained
parent and reserved final acceptance bank remain untouched.

The user's latest CPU ceiling is 80%. Corrected training's 122 two-second
whole-machine samples averaged 13.38%, with a maximum of 24.18%; auxiliary
evaluation's 52 samples averaged 14.30%, with a maximum of 22.29%. Hard transfer's
194 samples averaged 12.84%, with a maximum of 23.37%. These are
sampled windows, not bounds on shorter excursions. Runs use four engines, eight
allowed logical CPUs, nice +10 and CPU-only updates.

All local artifacts are under `logs/resource-collection-curriculum/` in the
implementation worktree. Complete review receipts are under `logs/audit/`:
`resource-collection-training-complete-independent-review.json` and
`resource-collection-economic-evaluation-complete-independent-review.json`.
The transfer review is
`resource-collection-hard-transfer-complete-independent-review.json`.

## Intermediate kill rewards and replay

The retained combat objective already pays intermediate rewards from increments
in enemy unit and structure value destroyed. The collection task deliberately
replaced that objective. In retained-parent Hard Protoss Air victory 112004,
45 nonzero kill-reward events contributed 0.5825 undiscounted reward before the
victory bonus and potential terms. This verifies actual intermediate feedback;
it does not establish that earlier production decisions receive useful credit.
Subsequent learning should retain combat feedback while testing economic retention.

That actual victory was replayed on Linux and exported to
`logs/replay-proof/retained-terran-hard-protoss-air-win.mp4`: 431 frames at 4 fps,
107.75 video seconds covering the complete 422.32-game-second replay, with no
frame cutoff. Export took 75.65 seconds. ffprobe and a decoded frame verify the
H.264 video and real SC2 terrain, buildings, units and combat. This is one
illustrative retained-policy win, not evidence that the rejected candidate won.

## Bounded follow-up diagnostic

The user suggested intermediate unit/building kill rewards. The next question
is whether those combat rewards and economic learning can coexist in the shared
actor. A training-only, zero-update check compared the first economic batch with
one eligible original-parent Medium combat batch, selected lexicographically by
provenance before computing gradients. Neither evaluation bank supplied labels.

Both actors and stored likelihoods matched the original parent exactly. With
task-local advantage normalization and one fixed 50/50 actor direction, the
local economic surrogate derivative was +0.002931799 and the combat derivative
was +0.000660563. Independent read-only reproduction matched every saved value
and verified all 19 input hashes. The shared body's combat derivative was only
+0.000003121, so compatibility there is fragile. There were no optimizer steps,
new games, fitted weights or mixture searches.

This supports testing one separately declared mixed-task learner while retaining
kill feedback. It establishes no Adam-update behavior, repeated-update stability,
gameplay improvement or Hard transfer. The diagnostic and its source/selection
are under `logs/resource-collection-curriculum/mixed-gradient-diagnostic/`; the
independent receipt is
`logs/audit/resource-collection-mixed-gradient-independent-review.json`.
The production parent and main CLI have not been promoted to this task model.
