# Joint entity imitation implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. The user authorized continuous execution without approval pauses.

**Goal:** Train complete raw commands from human examples with shared entity representations, then test whether the frozen model preserves construction and builds an army.

**Architecture:** Compact numeric entity features plus learned unit/order embeddings feed one shared encoder. Context includes all 32 stored commands with semantic features; ability, actor membership, unit/point target, queue and timing losses train that encoder together. Inference uses predicted ability and actor group; training/oracle diagnostics explicitly disclose teacher conditioning.

**Tech stack:** Existing NumPy CPU runtime, raw SC2 API, unittest. No dependency downloads.

**Spec:** `docs/learning-roadmap.md`; the Astra recommendation and nine-game comparison in `docs/learning-execution.md`.

## Global constraints

- Existing `.worktrees/terran-rl`, branch `Sam-v6/terran-rl`; preserve primary checkout and old models.
- CPU approximately 80% maximum, CPU-only training, no sudo or large unsolicited downloads.
- Human imitation first; all RL remains held until competent imitation.
- Full native ability/unit-group/target/queue/autocast grammar; no 27-choice strategy fallback.
- Nine complete Mez teaching games (3,543 commands); reused Lyra/Huski diagnostics are not fresh acceptance.
- 51483 and 51886 remain closed to model prediction/fitting until a complete candidate and protocol are frozen.
- Professional corpus, micro transfer and all-race Hard/higher difficulty remain required, uncompleted roadmap work.

## Review focus

- Entity order/tag changes must permute actor/target scores without changing scene decisions.
- Target and queue losses must update the shared encoder, not only isolated heads.
- Loaded own units and enemy memory must preserve causal actor knowledge without inventing visible target attributes.
- Spatial target candidates must cover the playable map; inserted gold targets or oracle masks must never leak into ordinary inference.
- Human actor groups, queue/autocast, timing masks and simultaneous bursts must be counted honestly in complete-command evaluation.

### Task 1: Compact shared encoder

**Files:** Create `src/learning/entity_encoder.py`; test `tests/test_entity_encoder.py`.

**Interfaces:** `JointEntityEncoder(features, scene_features, history_features, unit_types, abilities, hidden=32, seed=0)`. `forward(entities, unit_types, orders, scene, history, history_roles)` returns `(context, entity_embeddings, cache)`. `backward(cache, context_gradient, entity_gradient)` returns gradients for `parameters`.

- [x] Write failing tests for entity permutation, history older than two commands, empty entity state and finite-difference gradients from context and individual entity losses.
- [x] Run `.venv/bin/python -m unittest tests.test_entity_encoder -v`; require failures due to missing encoder.
- [x] Implement compact numeric projection, learned type/order embeddings and all-32-slot history context with analytic shared gradients.
- [x] Run targeted tests, suite and Ruff; commit verified core.

### Task 2: Joint complete-command model and causal examples

**Files:** Create `src/learning/entity_policy.py` and `src/learning/entity_examples.py`; tests in matching `tests/test_entity_*.py`.

**Interfaces:** Policy consumes encoder inputs, actor/target eligibility and spatial candidates. `predict` uses its own ability and selected group; `loss_and_gradients` uses explicit human labels and returns all joint gradients. Checkpoint save/load persists shared parameters and metadata. Examples consume `teacher_states` and existing fog-safe state fields.

- [x] Write failures for actor/pointer permutation, queue/target gradient reaching shared embeddings, masked unknown timing, checkpoint prediction equivalence and candidate coverage without gold-label insertion at inference.
- [x] Run those failures before production implementation.
- [x] Implement shared actor/group argument conditioning, categorical unit/point pointers, full ability/mode/queue/delay heads and compact causal preprocessing.
- [x] Numerically verify representative gradients through every active head; check full real command grammar and large uint64 actor/target identity.
- [x] Run suite/Ruff and commit model/preprocessing.

### Task 3: One fixed human supervised fit and full-command audit

**Files:** Create `src/learning/entity_train.py`, `src/learning/entity_audit.py`; tests for split enforcement and actual command decoding.

- [x] Write/run failures for whole-replay split collisions, incomplete datasets and evaluation using predicted actors/targets rather than oracle labels.
- [x] Implement CPU optimizer and streaming compact example collection. Freeze nine-game source/checkpoint bindings and one configuration/update budget before fitting; choose budget from a measured short throughput smoke run, not a parameter sweep.
- [x] Evaluate complete commands plus ability/actor-oracle diagnostics on teaching games and reused other-player diagnostics; report target candidate coverage and all excluded labels.
- [x] Stop before native play if teaching reconstruction remains poor. If reconstruction improves without other-player fidelity, prioritize broader player data instead of expanding architecture blindly.
- [x] Run suite/Ruff, independent review and commit verified implementation/results.

### Task 4: Frozen imitation-only native test

**Files:** Integrate opt-in model in `src/learning/imitation_play.py` and document execution/results.

- [ ] Write/run failures for checkpoint-selected joint inference, native command identity, legality handling and queue/autocast preservation.
- [ ] Implement an opt-in path using the complete joint checkpoint; keep old defaults.
- [ ] Freeze a VeryEasy all-race functional protocol before any fresh holdout prediction; check completed construction, sustained army and actual terminal outcomes. Do not manufacture recovery labels by attaching human actions to arbitrary student histories.
- [ ] Audit results and retain replay/trace/source hashes; do not show videos to the user before the overall goal completes.
- [ ] Promote only with supporting evidence. RL, Hard acceptance and professional/micro roadmap gates remain separate and open.

## Execution ledger

- Start: `68a7c8d`, clean worktree, all five extraction attempts/retries and expanded macro comparison terminal. No active training/native job.
- Ruling: implement inline under the user's instruction to keep working without approval pauses; no additional execution-method confirmation.
- Ruling: implement the jointly learned representation rather than patch the old dense actor collector. Compact entity features address its memory cost while connecting downstream losses; this costs a new model experiment and does not guarantee competence.

- Task 1: five missing-feature failures observed before implementation; two row-alignment tests then failed with ValueError not raised before guards were added. Seven targeted tests pass, including finite differences with repeated type/order/history IDs, permutation invariance, empty state and oldest-of-32 history sensitivity. Full suite: 194 tests, 9.769 seconds, all green. Ruff and diff checks pass.
- Task 1 smoke: `logs/roadmap/entity-encoder-smoke-01.json`; synthetic 200-entity/32-numeric-feature inputs, 1,970 unit slots and 3,801 ability slots, 1,000 forward/backward calls in 0.163 seconds including postchecks. Encoder parameters 881,536 bytes; numeric entity payload 25,600 bytes plus categorical payload 3,200 bytes. No optimizer update, human fit or native throughput claim.
- Ruling: pooled context plus separate entity embeddings is the first shared encoder; command heads, semantic state conversion, candidate coverage and actual queue/target-loss coupling remain Task 2. Old live/model defaults remain unchanged.

- Task 2: complete joint ability/actor/group/mode/queue/delay/unit-pointer/spatial-pointer heads added. All argument losses propagate through group conditioning and shared entity/history parameters. Spatial candidates cover the whole map rectangle in eight-unit cells, with learned continuous offsets within each cell; ordinary prediction never inserts a human point or actor group. Ability 0 is a sentinel and cannot become an issued command.
- Task 2: 13 targeted tests pass after missing-model/converter failures and an observed failure for unrepresentable burst targets. Central finite differences verify all command modes and representative parameters in every active head plus the shared encoder. Tests cover entity permutation, queue/target-label gradient coupling, unknown timing masks, checkpoint equivalence, uint64 tags, fog-safe memory, map edges and simultaneous bursts. Full suite: 207 tests in 9.796 seconds; Ruff and diff checks pass.
- Task 2 real audit: `logs/roadmap/entity-examples-real-audit-02.json`; all nine teaching games, 3,543 commands, 3,542 reversible complete labels, 15.198 seconds, before/after bindings unchanged. One command (51754 loop 3480, Attack ability 23, target 4367319041) has no observed target candidate; exclusion is explicit. All later commands still receive the actual human history. This is conversion coverage, not model accuracy. Reserved 51483/51886 and professional data were not opened.
- Ruling: replay iterator returns `(inputs, label, command, exclusion)`; an unrepresentable label is None with a reason, rather than terminating the game or inserting an unseen unit. Task 3 must count excluded labels against the total command denominator and report their reasons — preserves fog safety and all remaining training examples — costs one complete supervised label in this corpus.
- Task 2 payload: 94 numeric fields/entity (30 current-state/construction fields plus 32 actor/target history reference pairs), full engine type/order embeddings, nine semantic fields/history command and observed upgrade flags. Nine-game numeric entity payload totals 268,004,904 bytes; model parameters 1,447,856 bytes. These are component sizes, not measured trainer peak RSS or native speedups.
- Task 2 scope: one untrained analytic-gradient call per teaching game, no optimizer/model fit/native play/RL. Task 3 remains open and must bind/freeze its complete supervised configuration before the real fit.

- Task 3 in progress: seven missing trainer/auditor tests observed failing before implementation, then green. Includes replay-identity split collisions under different paths, partial/fog-disabled rejection, source digest inventory, actual joint supervised optimization, ordinary predicted actor evaluation versus named oracles, exclusion denominator and masked unknown timing. Full suite: 214 tests in 9.756 seconds, all green; Ruff/diff checks pass before fitting.
- Task 3 throughput smoke terminal: `logs/roadmap/joint-entity-throughput-01/report.json`, nine teaching games, one epoch/222 updates, 3,542 usable commands, 2.403 seconds fitting/19.259 seconds total. Unpromoted smoke checkpoint is not reused. Initial training reconstruction 5 complete commands is not competence evidence.
- Task 3 fixed experiment: `logs/roadmap/joint-entity-fit-contract-01.json`; fresh seed7000/7001 model, hidden32, uniform command sampling/shuffled epochs, batch16, rate0.001, 200 epochs/44,400 planned updates, 900-second fit bound and 1050-second caller bound, two BLAS/OMP threads. Reused Lyra50925 and Huski51960 diagnostics; no reserved51483/51886 prediction. Live handle at dispatch:23118; inspect that exact handle and authoritative output before deciding termination/restart.
- Task 3 teaching gate frozen before fit: ability95%, exact actor groups90%, complete commands75% with one-tile point tolerance; total denominator3543 includes the excluded label. Timing is reported separately. This is a reconstruction prerequisite, not a native/professional/Hard gate.
- Ruling: one independent fresh reviewer covers the whole newly implemented encoder/model/converter/trainer/auditor candidate while fitting; Task4 is not implemented and native play stays held — this follows Task3's explicit independent-review requirement and catches defects before interpreting/promoting the new architecture — costs one review before the final native integration review. Reviewer is read-only during frozen fit.

- Task 3 independent whole-candidate review: reviewer `/root/review_joint_imitation` found no actionable defect, ran 27 focused tests including finite differences, and confirmed predicted conditioning, causal bursts, exact tags, honest exclusion denominator and replay-identity splits. Review explicitly withheld terminal fit, fresh generalization, native competence and professional/playing-strength claims. Read-only; no code/source/reserved-data changes.

- Task 3 terminal fit: handle23118 exited0; `logs/roadmap/joint-entity-fit-01/report.json`, 200 full epochs, 44,400 updates, 483.316 seconds fitting/502.466 total, final loss0.970165, checkpoint SHA256 `e0cd9737fccf466c3b683bfc343b311c605b457e05f70ea4155ddf3f712541aa`; input/code/checkpoint bindings unchanged. No native/RL processes were started.
- Task 3 ordinary teaching: ability3540/3543 (99.915%), exact actor groups1563/3543 (44.115%), complete628/3543 (17.725%) at one-tile point tolerance. Timing3101/3493 (known labels); complete-with-timing612. Ability/actor oracle complete1679/3543 (47.389%). Frozen teaching gate fails: native play held, no fresh holdout use or promotion.
- Task 3 reused validation (Lyra/Huski combined): ability189/647 (29.212%), exact actor groups138/647 (21.329%), complete11/647 (1.700%); ability/actor oracle complete165/647 (25.502%). These are reused teacher-state diagnostics, not fresh generalization or student-history/native results.
- Task 3 reloaded verification: `logs/roadmap/joint-entity-fit-verification-01.json`; verified all200epochs/44400updates, regenerated ordinary field counts from the saved checkpoint, bindings unchanged, gatefalse, 18.585 seconds. Teaching actor errors:472 oversized groups,510 undersized groups,998 correct-size/wrong-member groups. Membership TP14236/FP2910/FN3663; per-eligible-entity BCE0.05884. Spatial oracle:1567/1970 correct cells (79.543%), but only304/1970 offsets within one tile even with the human cell (15.431%). This explicitly oracle diagnostic does not leak labels into ordinary prediction.
- Ruling: Task3 implemented/evaluated even though competence gate failed; Task4 native execution remains unperformed and must not be marked complete. Next bounded experiment should target weak actor-ranking supervision and cell-relative offset prediction/physical tile error, rather than another blind epoch sweep — failures persist with almost-perfect teaching ability and with supplied human actor groups — costs a deliberate revised objective/conditioning experiment before native play. Original professional/micro/Hard/higher-difficulty roadmap requirements remain open.
- Task 3 CPU sample during verified live fit:32logicalCPUs,6.575% whole-machine utilization over one second, two BLAS/OMP threads, CPU-only. This is a sample, not a peak-load guarantee. All fit/audit jobs are terminal at Task3 finish.
