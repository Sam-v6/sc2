# SCV credit estimator replay implementation plan

> Execute this bounded diagnostic inline, using the executing-plans workflow.

**Goal:** Test whether temporal credit or batch centering accounts for the locally
SCV-suppressing actor direction before proposing another gameplay experiment.

**Architecture:** Reuse the frozen 176-to-180 batch and fixed parent-state bank from
the completed SCV credit audit. Evaluate four predeclared credit variants at the
same behavior weights, with NumPy analytical gradients and no optimizer steps.

**Tech stack:** Existing Python, NumPy and low_load wrapper.

**Spec:** [SCV credit audit](2026-10-05-scv-credit-audit.md).

## Constraints and interpretation

Zero games, optimizer steps or checkpoint writes. One BLAS thread, CPU only,
existing eight-CPU affinity/nice wrapper; no installs. Keep all original source,
reward, discount, observations, masks, actions and behavior value predictions.
Use ignored `logs/scv-credit-estimator-replay/` for source and receipts.

Exactly four variants: full-match lambda=1 with centered/std-scaled advantages
(baseline); lambda=1 with std scaling only; lambda=.95 per game second with
centering/std scaling; lambda=.95 per game second with std scaling only. Use
lambda_i=.95**(next_decision_time-current_time); terminal continuation is zero,
so its duration is immaterial. Gamma stays at the existing per-decision value.
Do not fit a new critic or sweep lambda after looking at results.

Report early SCV/wait raw and transformed advantages, per-game contributions,
actor and weighted-critic local margin derivatives, gradient norms and value
targets. Negative directions are not failures of the mathematical implementation.
Baseline must reproduce the prior credit audit within numeric tolerance. A candidate
only qualifies for further consideration if its actor direction increases the
fixed-bank primary margin, mean transformed early SCV advantage is positive, and
at least three of the four games have positive early SCV means. This is a mechanism
gate, not a gameplay gate; crossing it cannot justify a strength claim or promotion.
If none qualify, close this comparison and inspect other supported mechanisms.

## Review focus

Preserve terminal handling; lambda=1 must reproduce completed Monte Carlo credit.
Do not center within action subsets or games: transformations use the full batch.
Avoid sibling encoder drift: reuse already verified cached project observations.
Do not confuse analytical full-batch gradients with actual multi-minibatch Adam.
Hash all inputs and implementation before reporting measurements.

## Steps

- [x] Add failing synthetic tests for lambda=1 equivalence, terminal continuation,
  elapsed-time trace decay, and actor-margin finite differences.
- [x] Implement `source/replay.py` with credit calculation and analytical gradients.
- [x] Freeze prior manifests, cached states, raw trajectories, checkpoint and source
  hashes into `inputs.json`, then run exactly the four comparisons under low_load.
- [x] Verify baseline against the independent prior audit and request independent
  review from the existing authorized reviewer; document results and next action.

## Completed result: no candidate qualifies

All four comparisons completed with zero games or optimizer steps. Five focused
tests pass. The initial synthetic Monte Carlo fixture contained a hand-calculated
arithmetic error; it was corrected to the explicit discounted sum, with the failure
retained. The baseline matches the prior audit's advantages and actor/critic
directions within 1e-12. Independent review reproduces all saved results exactly
and verifies elapsed decay, terminal handling, full-batch transformation and hashes.

| Variant | Actor margin direction | Mean early SCV transformed credit | Games with positive early SCV mean | Mechanism gate |
| --- | ---: | ---: | ---: | --- |
| Full-match, centered | -.108427 | -.274880 | 1/4 | Failed |
| Full-match, std only | -.163288 | +.882050 | 4/4 | Failed |
| GAE .95 per second, centered | +.009879 | -.413951 | 0/4 | Failed |
| GAE .95 per second, std only | +.000766 | -.221781 | 0/4 | Failed |

Removing the mean does not repair the local actor direction despite making SCV
credit positive. The shorter trace reverses that direction but still gives early
SCV choices negative credit. No variant meets all three predeclared checks, so this
comparison closes without a gameplay arm, parameter sweep or promotion. These
results do not prove that temporal credit cannot help on another batch or with a
better critic. They contradict the simple explanations tested here.
The positive-SCV requirement is a hypothesis filter, not ground truth that every
early SCV choice is useful. Selecting an estimator to enforce our preferred action
would be circular. Astra therefore recommends direct paired environment outcomes
for individual alternatives, under the retained greedy continuation, as the next
[exploration pilot](2026-10-05-one-decision-exploration.md).

Artifacts: `logs/scv-credit-estimator-replay/inputs.json`, `results.json`,
`tests-green.stdout`, and `logs/audit/scv-credit-estimator-independent-review.json`.
The retained main policy and every input checkpoint remain unchanged. Astra has
been asked for the next supported path, including the mismatch between strong
parent greedy Medium play and weak stochastic training collection.
