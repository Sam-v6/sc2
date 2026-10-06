# Human imitation context normalization implementation plan

> **For agentic workers:** Use superpowers:executing-plans to implement the
> steps in the existing isolated worktree. The user authorized autonomous
> execution; no additional plan approval is required.

**Goal:** Test whether the measured context saturation impedes learning from
the existing professional human examples.

**Architecture:** Normalize only the combined encoder context before its tanh,
per example across hidden dimensions. Fixed gain one and bias zero isolate the
change. An opt-in flag preserves every existing default and checkpoint.

**Tech stack:** Existing NumPy encoder, handwritten derivatives, unittest.

**Spec:** `docs/learning-execution.md`; frozen fit05 and
`logs/roadmap/professional-encoder-saturation-01.json`.

## Global constraints

Human supervised learning only; RL stopped. CPU-only, approximately 80% ceiling,
BLAS/OMP two threads. No downloads, sudo or native games for this experiment.
Use nine corpus07 teaching games and reused diagnostic774 only. Reserved848 and
51483/51886 are excluded from fitting and predictions. Preserve fit05 and its
supported-input derivative. No simultaneous architecture/data/loss changes.

## Review focus

Near-constant context must have finite, correct derivatives.
Every scene/pool/history/bias branch must receive the normalized gradient.
Absent/false flags must preserve old initialization and both derivative paths.
Saved checkpoints must preserve the flag without changing parameter shapes.
Reduced saturation alone is not evidence of better command decisions.

## Task 1: Optional normalization with verified derivatives

Files: `src/learning/entity_encoder.py`, `src/learning/entity_policy.py`,
`src/learning/entity_train.py`, `tests/test_entity_context_normalization.py`.

Interface: add `context_layer_norm=False` to the encoder constructor. Persist
that boolean in checkpoint configuration and load absent values as false. Add
`--context-layer-norm` to the trainer and bind it in experiment configuration.
Do not add parameters or change initialization draws.

- [ ] Write tests and observe their failure before implementation. Cover
  finite differences through scene, pool, history and context bias, including a
  nearly constant context. Cover false/default parity and checkpoint roundtrip.
  Use this numerical-gradient check against the actual encoder forward/backward:

  ```python
  parameter[index] = original + epsilon
  plus = objective(encoder.forward(*inputs))
  parameter[index] = original - epsilon
  minus = objective(encoder.forward(*inputs))
  parameter[index] = original
  numeric = (plus - minus) / (2 * epsilon)
  np.testing.assert_allclose(analytic[index], numeric, rtol=.01, atol=.001)
  ```

- [ ] Implement only the opt-in branch, caching normalized context and inverse
  standard deviation. Here `z` is the existing summed context projection:

  ```python
  centered = z - z.mean()
  inverse = 1 / np.sqrt(np.mean(centered**2) + 1e-5)
  normalized = centered * inverse
  context = np.tanh(normalized)
  g = context_gradient * (1 - context**2)
  dz = inverse * (g - g.mean() - normalized * np.mean(g * normalized))
  ```

  The disabled path must retain the old calculations exactly. Pass `dz` into
  every existing context branch derivative. Keep entity and downstream heads
  unchanged. Centering/normalizing removes common mean and magnitude information;
  this is an architectural tradeoff, not a proven correction.

- [ ] Run focused tests, then `OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2
  PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -q`, Ruff and
  `git diff --check`. Independently review derivatives/default compatibility.

## Task 2: One matched human-training comparison

Files: ignored experiment helpers/receipts under `logs/roadmap/`; update this
plan and `docs/learning-execution.md` with terminal evidence.

- [ ] Freeze configuration before fitting: fit05's exact nine sources, counts,
  seed8100, hidden32, batch16, rate.001, refinement, actor cutoff, spatial,
  availability, role pooling and actor-relative points. Add only context
  normalization. Use50epochs/14100updates and600optimizer-second wall bound.
  If the wall bound prevents the matched update count, report that limitation;
  do not silently call it a matched comparison or extend the budget.

- [ ] Fit once, preserving source/code/checkpoint hashes. No extra epochs,
  epsilon/gain sweep, alternate initialization or data expansion.

- [ ] Recompute both checkpoints' total supervised loss on identical teaching
  commands, with ability, actor, mode, queue, timing, target and point-offset
  contributions separately. Check the component sum against the existing
  `loss_and_gradients` total; use read-only instrumentation, not a new objective.
  Report complete copying per teaching game and ordinary diagnostic copying.

- [ ] Apply all gates: total teaching loss at least20% lower; complete teaching
  matches at least1277/4513 (ten percentage points above825), improvement in at
  least7of9games; ordinary diagnostic complete at least24/292; diagnostic
  ability/actor accuracy each no more than five percentage points below fit05
  (149/292 and53/292). Report saturation for explanation only.

- [ ] Record outcome without promotion or RL. Teaching-only improvement means
  optimization improved but transfer remains unresolved. Failed teaching gates
  reject this intervention as the next useful step. Either outcome ends this
  experiment; do not start a normalization/optimizer sweep. Whole-game native
  competence, learned micro transfer and reliable all-race Hard wins remain
  separate unproved requirements of the active full roadmap.

## Execution record

Task1: Five tests observed failing on the absent constructor flag, then passing.
Full317tests pass in9.97seconds; Ruff and diff checks pass. Independent Astra
review checks exhaustive parameter finite differences with role pooling, direct
entity gradients and nearly constant nonzero variance. It also verifies exact
base08bd929/current disabled initialization, forward/backward parity for both
pooling paths, and actual fit05/supported checkpoint compatibility. No blocker.
Final: minor (deferred): retain the reviewer's role-pooling and nearly constant
nonzero-variance cases in committed tests; reviewer checked them independently.
No additional implementation change is justified before the fixed comparison.
No rulings changing the intervention or experiment bounds.

Task2 contract is written before launch by
`logs/roadmap/run_professional_context_fit_01.py`, binding exact source/checkpoint/
code and gates. Output is `logs/roadmap/joint-professional-fit-06/`.
