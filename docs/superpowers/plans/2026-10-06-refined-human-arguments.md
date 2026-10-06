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

- [x] Freeze fresh seed7000/7001, hidden32, batch16, rate0.001,200epochs/44400updates,900second fit wall bound, same datasets, refinement=True before fit. Bind current code, datasets, baseline checkpoint and comparison protocol. No epoch/rate/architecture sweep.
- [x] Run fixed CPU-only fit; monitor exact live handle until terminal. Do not modify bound production code during fit.
- [x] Reload both checkpoints, regenerate ordinary full-command counts and explicit human-cell offset/ranking diagnostics. Compare same cohort and total denominators. Record source/checkpoint bindings before/after.
- [x] Independent whole-change review, record material limitations, commit verified implementation and results. If teaching gate fails, hold native/RL and derive next action from field-level evidence. If it passes, proceed to the existing frozen native functional protocol without claiming full roadmap completion.

## Execution ledger

- Previous turn classified as progress: commit `b497bb8`, supervised fit44400updates terminal, failed teaching gate independently regenerated from the saved checkpoint. No live fit/native process at start of this plan.
- Ruling: execute inline without an approval pause under the user's explicit instruction to pursue the goal. This bounded experiment tests two concrete hypotheses; they are not asserted as proven causes.

- Task1: seven missing-refinement failures observed before implementation. Seven targeted tests now pass, including every-mode central finite differences, candidate permutation, predicted-vs-explicit human cell behavior, physical radii loss/gradients, selected-set ranking and legacy/refined checkpoint roundtrip. Full suite221tests in9.808seconds passes; Ruff/diff checks green.
- Task1 compatibility: `logs/roadmap/refinement-baseline-compatibility-01.json`, all nine teaching and both reused diagnostic games; the old checkpoint's entire report (including all oracles/geometry metrics) regenerated exactly in19.211seconds. Original checkpoint SHA and dataset bindings unchanged. Historical original code hashes are deliberately not claimed unchanged after this modification.

- Task2 dispatched: `logs/roadmap/joint-entity-fit-contract-02.json`, exactly the baseline200epoch/44400update recipe, same9teaching/2reuseddiagnostic sources; refinement=True, fresh initialization. Baseline checkpoint `e0cd9737fccf466c3b683bfc343b311c605b457e05f70ea4155ddf3f712541aa` is comparison only, not resumed. Live handle93461; follow that exact handle until authoritative terminal evidence. Current bound production files must not change during fitting.
- Task2 review: fresh read-only reviewer `/root/review_refined_arguments` checking the whole change while fitting. No extra fit, native game, download or reserved-data access authorized.

- Whole-change review: `/root/review_refined_arguments` found no material defect;14targeted tests and additional exhaustive partial/full/noncontiguous-group and anisotropic-radius finite differences passed (maximum absolute error2.04e-9). The latter cases are now persisted as an eighth targeted test. Raw training losses differ across objectives and must not be compared as equivalent; combined refinements cannot yield component-specific attribution. No production edits during the frozen fit.

- Coverage after review: eight refinement tests and full222-test suite pass (9.916seconds). Persisted finite differences now include multi-actor partial/full groups, noncontiguous eligible masks and anisotropic edge-cell radii. All bound production files remain atd46eaa2; only tests/plan changed during the live fit. Fit still nonterminal at last handle93461 poll; compare helper `logs/roadmap/compare_joint_refinement_01.py` is prepared but must run only after completed report/full44400updates.

- Task2 terminal: handle93461 exited0; `joint-entity-fit-02/report.json` completed200epochs/44400updates,518.106seconds fit/537.437total, checkpoint SHA256 `95167fc48ca862eca5b118bc106fc20bdb20a0e7e51bec785e12ce4052a4924e`, bindings unchanged at completion. Comparison handle92561 exited0, `joint-refinement-comparison-01.json`, exact reloaded audit regeneration,24.372seconds; frozen teaching gatefalse.
- Same-cohort teaching ordinary baseline->refined: ability3540->3532/3543; actors1563->2033; complete628->1495 (17.7%->42.2%). Human ability/actors supplied: complete1679->2542/3543. Explicit human-cell offsets304->1754/1970 within one tile, while correct cells1567->1224/1970. Actor oversized groups472->1000, undersized510->368, same-size wrong members998->142. Ranking/residual gains coexist with cardinality/coarse-cell costs; no component-specific causal attribution.
- Reused Lyra/Huski ordinary ability189->174/647; actors138->89; complete11->9. Cross-player fidelity did not improve. Next priority is player diversity with the refined architecture held fixed, not another architecture sweep. No native/RL/fresh reserved prediction.
- Correction: both fit contracts selected the older unmasked Huski diagnostic path. Seven timing labels crossed unresolved human commands. `joint-refinement-timing-diagnostic-correction-01.json` verifies corrected rows differ ONLY in timing; all non-timing counts/point errors are identical for both checkpoints. No teaching label or model weight is affected. Corrected known-timing denominator633 (previous640), ordinary baseline delay143 (previous146), refined114 (previous116); complete-with-timing2/3 unchanged. Original reports remain historical; corrected receipt supersedes their timing counts.
- Timing safeguard: one regression failed ValueError-not-raised before a dataset validator guard. It now rejects labeled gaps crossing unresolved events, accepts masked gaps and exact boundary events. Full225tests in9.815seconds and Ruff/diff checks pass. Production modification happened only after fit/comparison/correction handles were confirmed terminal.
- Prospective diversity split audited, no fit/prediction: `multiplayer-teacher-split-contract-01.json` and `multiplayer-teacher-split-audit-01.json`;11teaching games/4190commands/4189representable from Mez3543, Lyra342, Huski305 (corrected timing); Rom180commands stays diagnostic. Previously reused Lyra/Huski explicitly move to teaching before any next fit. This is not randomized fresh acceptance. Professional teachers0, reserved51483/51886 closed. Source/code bindings unchanged at collection audit.
