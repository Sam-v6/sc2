# Diverse human imitation experiment

**Goal:** Test broader player coverage after refined teaching reconstruction improved without other-player fidelity. Full professional/native/micro/Hard/higher-difficulty requirements remain open.

**Spec:** `docs/learning-roadmap.md`, terminal refined comparison and prospective split audit in `docs/learning-execution.md`.

**Scope:** No architecture/loss/optimizer changes. Existing isolated worktree `terran-rl`, branch `Sam-v6/terran-rl`, baseline commit337bb3f. CPU-only two threads, approximately80% machine ceiling, no downloads/sudo. Human imitation first; all RL held.

- [x] Verify11terminal/fog-safe/masked teaching sources:4190commands/4189representable, three named humans. Explicitly move reused Lyra/Huski diagnostics into teaching before fit; keep Rom180commands separate. Reserved51483/51886 closed, professional teachers0.
- [x] Freeze fresh seed7000/7001, hidden32, batch16, rate0.001, refinement=True, uniform shuffled commands,169epochs/44278updates,900second fit bound/1050caller bound. Expected707941example passes versus708400before (0.065%less),122fewer updates (0.275%less); approximately compute matched, not identical budget or proof of data-only causality.
- [x] Run exact frozen fit, poll its live handle until terminal, and do not modify bound production files during fitting.
- [x] Reload both current/refined baseline checkpoints on identical expanded teaching/Rom diagnostic cohorts. Count all excluded labels in full-command denominators, report each player separately and compare geometry/group-size errors honestly. Reused role changes are not randomized fresh acceptance.
- [x] Validate source/code/checkpoint bindings and full update budget, record evidence and decision. Ability95%, exact groups90%, complete75% at one-tile tolerance remain a teaching prerequisite. If it fails, no native/RL/fresh reserved predictions; derive next work from field-level evidence, not an unplanned sweep.

## Ledger

- Prior turn is progress: refined200epoch fit terminal with exact comparison; teaching complete628->1495/3543, cross-player11->9/647. Unmasked Huski diagnostic timing corrected and a225-test-verified validator guard added. No teaching/model change from that correction.
- Split contract/audit: `logs/roadmap/multiplayer-teacher-split-contract-01.json`, `multiplayer-teacher-split-audit-01.json`. Prospective sources inspected and bound before any fit of this split.
- Ruling:169epochs nearly match both command-pass/update budgets without adding a new trainer option or sweeping rates/widths. Added teachers are the main experimental change; epoch count adjusts for sample count. Validation role also changes, so compare checkpoints on common cohorts rather than unlike headline validation scores.

- Dispatched exact contract `logs/roadmap/joint-entity-fit-contract-03.json`; live handle64220. Output `logs/roadmap/joint-entity-fit-03`. Both previous fit/comparison/correction/source-audit handles are terminal. Follow64220, do not restart based on a missing report/progress-only file. No bound production edit during this fit.

## Terminal evidence and next decision

Fit64220 and comparison19478 ended successfully. All169epochs /44278updates /707941example presentations completed; source/code/checkpoint bindings held. Checkpoint SHA256 `87d3d072ed92b7525c2e43775d467c0ad36e7d2ca4a0049f5d9da581e60f3feb`. Comparison receipt: `logs/roadmap/diverse-human-fit-comparison-01.json`.

On identical expanded teaching data, complete commands change1504->1418/4190; exact groups2122->2232, ability3706->4162. Per-player complete commands: Mez1495->1173/3543, Lyra6->125/342, Huski3->120/305. Rom diagnostic complete6->7/180, exact groups63->45. Added teachers are learned but aggregate reconstruction and independent-player competence do not improve materially. Teaching gate fails; no promotion/native/RL/reserved evaluation.

A bound terminal actor diagnostic50173 supplies human ability and, separately, human cardinality. Exact groups improve2238->3545/4189 representable teaching commands when taking the highest-ranked K units rather than using zero as the cutoff. Rom improves61->102/180 with these explicit oracles. Receipt: `logs/roadmap/actor-cardinality-audit-01.json`. This does not demonstrate an autonomous cardinality predictor. Next bounded candidate: a context-conditioned shared actor-logit bias, preserving arbitrary group sizes and ranking while learning the selection cutoff. Verify gradients and unchanged legacy checkpoints before freezing a same-split supervised comparison. Spatial cells remain weak1031/2302 with human ability/group; fixing cardinality alone cannot establish full-command competence.
