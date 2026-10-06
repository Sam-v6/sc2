# Preserve native unit-type status in human imitation

## Hypothesis and scope

The saved-model audit finds weak teaching macro fit for ownership-wide linear
state summaries, while command-history fits memorize teaching sequences but
transfer poorly. Basic opening mistakes have observed producer queues and
resource/count information available. Preserve type-specific current status as
an additional learned context input to the full goal-first controller. This is
one representation intervention, not a narrowed action list or scripted macro.
The closed linear probe's incomplete convergence does not prove state absent.

## Implementation

- Add a masked, permutation-invariant own-unit summary for every native type:
  observed/memory counts; build-progress, order-count and first-order-progress
  means with explicit availability fractions; known idle fraction; known
  unfinished fraction. All ten columns use current causal fields only, never
  command-history references or human labels. Memory contributes count only.
  Enemy/neutral units cannot affect own status; existing full entity context
  preserves other observations. Count features use log1p/5.
- Optional `type_status` projection adds this vector to existing context.
  Initialize new projection weights to zero after existing initialization,
  preserving initial ordinary predictions and all old checkpoint behavior.
  Save explicit configuration; older NPZ files load with optionfalse.
  Require compatible raw94/188field layout when enabled.
- RED/GREEN tests: exact values, unavailable-field poisoning, memory/ownership,
  permutation/history invariance; learnable finite projection gradients,
  zero-initialization/base-weight parity, checkpoint reload and native adapter.
- Independent implementation review and relevant normal/optional tests.

## Next bounded paired human experiment (not yet launched)

Fresh paired controllers, identical base seed/teaching shuffle/objective and
training data; one has the zero-initialized extra projection. Six teaching games
294/870/955/839/991/523; hold887/920/851from both fits. Their previous diagnostic
use is disclosed: this is development generalization, not fresh acceptance.
No774or reserved848/51483/51886inputs or predictions. Original causal human
history/world states/labels; no history corruption or policy-generated states.
30epochs or600optimizer seconds per arm, batch16, Adam.001, seed8156;
2CPUthreads, noGPU/install,80%whole-host guard. Stop each arm at bound; no
extensions or hyperparameter sweep. Freeze wrapper/source/runtime/gates before
fitting. Ordinary inference plus own-prediction-history diagnostics, never
teacher forcing as acceptance. Report ability/macro recall/false positives,
complete commands and per-game counts, including unresolved command exclusions.

Gate: candidate improves held exact macro ability recall by10percentage points,
held complete commands by5percentage points, without raising held macro false
positives more than5percentage points; own-history held macro recall also gains
10points. Both runs must complete the same30epochs for a matched comparison.
A passing development gate warrants a separate functional full-game check,
not promotion or Hard acceptance. Failure yields one source/behavior inspection,
not repeat fitting. Actual micro transfer/RL/Hard/higher difficulties stay open.
