# Test transferable human action-choice signal before another controller fit

## Evidence

User-authorized Astra consultation follows repeated unsuccessful imitation
changes. Mixed-history own predictions on reused774 are243Smart,45Attack,
4TrainSCV and no other abilities. Human labels contain157Smart;160correct
abilities barely beat Smart-only157, and only2/91macro abilities match. This
is intention collapse, not solely an exact actor/point matching failure.
Parent independently reproduced these counts and native ability names.

Changing past commands while preserving human world states is an offline
corruption experiment, not an environment-consistent rollout. Removing history
from a model trained with history is distribution shift; it does not prove that
a state-trained model cannot learn. Astra advice is a hypothesis, not evidence
of competence. Wait for terminal mixed-trial verification before running this
probe. Preserve all completed failed artifacts; no controller extension or RL.

## One frozen bounded diagnostic

- Nine teaching games only. Three whole-game validation folds:
  (294,887,920), (870,839,851), (955,991,523); each uses the other six to fit.
  No774or reserved848/51483/51886inputs/predictions or model selection.
- One regularized multinomial linear classifier, three prespecified input arms:
  current masked state; actual causal human command history; both concatenated.
  State includes existing player scalars/upgrades, ownership-separated native
  unit-type and first-order counts, and availability indicators. History keeps
  the32event ability/role sequence and unknown-event indicators. No current
  actors/targets, game identity, future information or end-game statistics.
- Fit scaling and class statistics on each training fold only. Use all
  demonstrated ability IDs; explicitly count held labels absent from training.
  This is an ability diagnostic; the full gameplay action grammar is unchanged.
- Fixed objective: mean multinomial cross-entropy plus0.01/2times squared
  non-bias weights; deterministic training-frequency bias initialization.
  Training-only RMS scaling and nonzero-column selection; L-BFGS-B at most
  100iterations, ftol1e-9/gtol1e-5/maxcor10, no class weighting. Model classes
  come from training labels only; held absent classes always count as errors.
  Reported cross-entropy uses a1e-12probability floor, including present classes.
  Combined
  preparation/fitting wall bound300seconds, two CPU threads, no GPU/install.
  Failure to converge within bounds makes the relevant result inconclusive.
- Report held-game cross-entropy, top1/top3accuracy, macro recall/false-positive
  rate, per-ability counts, absent training abilities and training-frequency
  baseline. Inspect a fixed first three failed macro rows per validation game
  against original observations, without altering features or refitting.
- Positive state-only signal requires macro recall>=25%, at least10percentage
  points above history and frequency baselines in two of three folds, and macro
  false-positive rate<=10%. Passing is transferable action-choice evidence only.
  It is not complete-command imitation, native competence or Hard acceptance.

## Implementation and verification

- [x] Implement/test causal feature conversion and fold-only preprocessing.
- [x] Test bounded solver behavior, class coverage and independent metrics.
- [ ] Freeze runtime/source/configuration bindings and independent review.
- [ ] Run the single diagnostic after prior verification; independently check
  outputs. Use failures to audit source/coverage before another architecture.

If state-only passes, prioritize state-conditioned intention representation.
If both materially outperform state-only, investigate temporal observation
modeling with truthful history. If all arms fail, a linear probe cannot establish
unlearnability; source/coverage evidence is needed. The full roadmap, learned
micro transfer, native playback adapter, Hard panel and higher difficulties
remain open.

Implementation review finds no blockers. Unknown/current-command values do not
enter state features; history preserves unknown/present slots. Expired fits
report wall_bound and cannot count as positive signal. Corpus execution and
wrapper review remain pending; tiny tests establish mechanics only.
