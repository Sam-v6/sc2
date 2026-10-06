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

- [ ] Write failures for actor/pointer permutation, queue/target gradient reaching shared embeddings, masked unknown timing, checkpoint prediction equivalence and candidate coverage without gold-label insertion at inference.
- [ ] Run those failures before production implementation.
- [ ] Implement shared actor/group argument conditioning, categorical unit/point pointers, full ability/mode/queue/delay heads and compact causal preprocessing.
- [ ] Numerically verify representative gradients through every active head; check full real command grammar and large uint64 actor/target identity.
- [ ] Run suite/Ruff and commit model/preprocessing.

### Task 3: One fixed human supervised fit and full-command audit

**Files:** Create `src/learning/entity_train.py`, `src/learning/entity_audit.py`; tests for split enforcement and actual command decoding.

- [ ] Write/run failures for whole-replay split collisions, incomplete datasets and evaluation using predicted actors/targets rather than oracle labels.
- [ ] Implement CPU optimizer and streaming compact example collection. Freeze nine-game source/checkpoint bindings and one configuration/update budget before fitting; choose budget from a measured short throughput smoke run, not a parameter sweep.
- [ ] Evaluate complete commands plus ability/actor-oracle diagnostics on teaching games and reused other-player diagnostics; report target candidate coverage and all excluded labels.
- [ ] Stop before native play if teaching reconstruction remains poor. If reconstruction improves without other-player fidelity, prioritize broader player data instead of expanding architecture blindly.
- [ ] Run suite/Ruff, independent review and commit verified implementation/results.

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
