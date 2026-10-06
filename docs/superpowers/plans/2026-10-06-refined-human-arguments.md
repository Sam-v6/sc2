# Refined human actor and spatial supervision plan

> **For agentic workers:** Use superpowers:executing-plans inline. The user authorized continuous work without approval pauses. Task3 of the joint entity plan is terminal with a failed competence gate; this experiment precedes native Task4.

**Goal:** Improve complete-command imitation by addressing weak exact actor selection and inaccurate within-cell target positions.

**Architecture:** Retain the shared entity encoder and broad command grammar. Add a selected-set ranking loss alongside membership BCE, and condition continuous offsets on the chosen cell coordinate. Measure spatial residual loss in actual tile units. Preserve baseline checkpoint behavior through an explicit checkpointed refinement flag; one combined experiment cannot attribute gains to either component separately.

**Tech stack:** Existing NumPy CPU runtime/unittest; no downloads.

**Spec:** `docs/learning-roadmap.md`, terminal fit/verification `joint-entity-fit-01` and the bottleneck analysis in `docs/learning-execution.md`.

## Constraints and review focus

- Existing `.worktrees/terran-rl`, branch `Sam-v6/terran-rl`; initial commit `b497bb8`.
- Human imitation only, CPU approximately80% maximum, two CPU threads, no GPU/sudo/downloads.
- Same nine Mez teaching games/3543commands, same reused Lyra/Huski diagnostics. Reserved51483/51886 stay closed.
- Ordinary offsets use the model's predicted cell. Human cell conditioning occurs only in supervised loss/explicit oracle scores.
- Selected-set ranking uses every eligible own actor and every human selected actor, with no fixed group size, cardinality recipe or target leakage.
- Frozen criterion remains ability95%, exact groups90%, complete75%, one-tile point tolerance, total-command denominator including exclusions. Professional/micro/native/Hard goals remain unmet.
- Cells at map edges may have different radii; convert each coordinate error with the correct candidate radius before squaring/backpropagating.
- Legacy checkpoints must retain their existing outputs; refined checkpoints must preserve the new conditioning and loss flag through save/load.

## Task 1: Tested refinement core

Modify `src/learning/entity_policy.py`, `src/learning/entity_train.py`; add `tests/test_entity_refinement.py`.

- [x] Write/run failures for different-cell offsets, ordinary predicted-cell selection, physical-radius loss/gradient, legacy/refined checkpoint equivalence, all-mode numerical gradients and cell permutation.
- [x] Add constructor/checkpoint flag `refinement=False`. Refined head adds `offset_cell` (2x2). `_forward(..., point=None)` chooses its own argmax cell unless explicit teacher conditioning is supplied. Offsets: `tanh(arguments @ offset + points[cell] @ offset_cell + offset_bias)`.
- [x] For point labels only, use human cell in supervised forward and loss `.5 * sum((offset_error * point_radii[cell])**2)`. Differentiate radii squared and route argument gradients through shared encoder as before.
- [x] Add actor ranking KL: `logsumexp(eligible_logits) - mean(selected_logits) - log(selected_count)`, with gradient `softmax(eligible_logits) - selected_indicator/selected_count`. Existing BCE still trains membership threshold; no inference group restriction.
- [x] Add `--refinement` to trainer and freeze it in experiment metadata/checkpoint.
- [x] Run targeted/full tests, Ruff/diff checks; preserve old checkpoint predictions on the old teaching cohort.

## Task 2: One comparable fixed fit and reconstruction decision

- [ ] Freeze fresh seed7000/7001, hidden32, batch16, rate0.001,200epochs/44400updates,900second fit wall bound, same datasets, refinement=True before fit. Bind current code, datasets, baseline checkpoint and comparison protocol. No epoch/rate/architecture sweep.
- [ ] Run fixed CPU-only fit; monitor exact live handle until terminal. Do not modify bound production code during fit.
- [ ] Reload both checkpoints, regenerate ordinary full-command counts and explicit human-cell offset/ranking diagnostics. Compare same cohort and total denominators. Record source/checkpoint bindings before/after.
- [ ] Independent whole-change review, record material limitations, commit verified implementation and results. If teaching gate fails, hold native/RL and derive next action from field-level evidence. If it passes, proceed to the existing frozen native functional protocol without claiming full roadmap completion.

## Execution ledger

- Previous turn classified as progress: commit `b497bb8`, supervised fit44400updates terminal, failed teaching gate independently regenerated from the saved checkpoint. No live fit/native process at start of this plan.
- Ruling: execute inline without an approval pause under the user's explicit instruction to pursue the goal. This bounded experiment tests two concrete hypotheses; they are not asserted as proven causes.

- Task1: seven missing-refinement failures observed before implementation. Seven targeted tests now pass, including every-mode central finite differences, candidate permutation, predicted-vs-explicit human cell behavior, physical radii loss/gradients, selected-set ranking and legacy/refined checkpoint roundtrip. Full suite221tests in9.808seconds passes; Ruff/diff checks green.
- Task1 compatibility: `logs/roadmap/refinement-baseline-compatibility-01.json`, all nine teaching and both reused diagnostic games; the old checkpoint's entire report (including all oracles/geometry metrics) regenerated exactly in19.211seconds. Original checkpoint SHA and dataset bindings unchanged. Historical original code hashes are deliberately not claimed unchanged after this modification.
