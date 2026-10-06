# Retained command history implementation plan

> **For agentic workers:** Use superpowers:executing-plans for inline execution. The user has authorized autonomous roadmap work; no routine approval pause.

**Goal:** Give professional teaching and prediction-derived history the same causal command-window definition.

**Architecture:** Rebuild entity references and event embeddings from at most32prior retained commands. Teaching uses exact past human commands; evaluation uses past predictions. Both reset per game and preserve non-history observations, map patches, candidates, labels and exclusions. Current/future labels never enter current inference.

**Tech stack:** Existing NumPy/Torch CPU runtime and safe NPZ artifacts.

**Spec:** `docs/learning-roadmap.md`, `docs/learning-execution.md`, terminal `professional-goal-first-01/verification.json` and `retained-history-oracle.json`.

## Global constraints

- Preserve full action vocabulary, fog-safe observations and the full roadmap.
- CPU-only; no sudo, installs, asset acquisition, reserved predictions or RL.
- The current trial is terminal and failed; do not extend or mutate its artifacts.
- Preserve the worktree/branch and retained NumPy default controller.
- Representation alignment does not establish native competence or solve every generalization failure.

## Review focus

- Current/future command cannot appear in current inputs.
- An excluded label still represents a known past issued command.
- A new game resets history; old human event-slot history is removed.
- Base observations/candidates/spatial patches remain equal.
- Source rows match examples chronologically and count exactly.

### Task 1: Shared causal history rebuilding

**Files:** `src/learning/goal_first_train.py`, `tests/test_goal_first_train.py`.

**Interfaces:** Add `retained_history_examples(examples, rows, vocabulary, products)` returning existing `(inputs,label,command,exclusion)` tuples. Preserve `prediction_history_examples(policy, examples, rows, vocabulary, products)` API/results. Both consume normalized `(row,state)` from `teacher_states`.

- [x] Add a failing three-row test with stale human history and excluded labels. Empty row0 history; only previous retained commands at rows1/2. Changing the last command leaves all current inputs unchanged; a new call resets history. Preserve arrays/labels and reject reversed/misaligned rows.
- [x] Run the new optional CPU test: missing-function RED.
- [x] Extract shared row alignment/non-history input checks. Teacher helper calls `remember_command` after storing current rebuilt inputs:

```python
remembered = dict(remember_command(command.as_dict(), observed, row['action_loop']), verified=True)
history = [*history, remembered][-32:]
```

- [x] Run optional controller/trainer tests, normal default suite, Ruff and diff checks. Compare a professional game's new teacher inputs/predictions against the saved retained-history oracle; prediction history still reproduces saved records.
- [x] Independently review leakage, exclusions, reset/alignment and old prediction-history parity before fitting. Commit source/tests/evidence.

### Task 2: Freeze a representation-only experiment after Task1 passes

**Files:** Ignored run/watch/check helpers under `logs/roadmap/`; execution ledger.

- [ ] Same controller,9teaching games/774reused diagnostic and command labels. Fresh single fit/output/hashes; no architecture/loss/sampling sweep.
- [ ] Retain all eight copying gates. Additionally require own-history teaching complete>=1000/4513 and own-history diagnostic ability>=170/292,actors>=73/292,target>=62/292,complete>=24/292,macro ability>=20/91. Human-state reconstruction alone cannot promote native policy.
- [ ] Bind retained-history teaching, code/runtime/support/baseline/source hashes;100epochs/1800optimizer seconds, Adam.001/batch16/modelseed8140/shuffle8142/two CPU threads/80%host guard.
- [ ] Evaluate all exact fields/timing/families, independently reproduce predictions and compare retained-gold vs predicted history. Reserved games untouched.
- [ ] Failure ends without extension/native/RL. Any later intervention follows verified evidence; the roadmap still requires learned micro transfer, reliable all-race Hard wins and higher evaluation.
