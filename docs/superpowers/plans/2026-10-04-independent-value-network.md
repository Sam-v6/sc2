# Independent value-network experiment

The game-held-out value-feature diagnostic passed its engineering gate and
independent review. Test whether a separately trained value representation
improves actual PPO learning. This is a combined value-body/optimizer-separation
experiment; it does not isolate a single cause of previous losses.

Copy the original-rate near-greedy source. Retain its5460 observations,27 actions,
Win1000 objective, temperature0.05, rate0.0003, finite lambda1/gamma, cadence,
worker execution and combat behavior. Do not include declared-race flags or
any offline fitted arrays. Add a separate64-unit tanh value body, cloned from
the untouched actor body at migration, and the existing value head. The actor
forward path and categorical probabilities must remain numerically equivalent.
Avoid computing the value body when only action probabilities are needed.

Migrate untouched near-greedy initial03633df9… with an explicit new checkpoint
schema. Preserve the actor parameters, Adam moments/step, RNG and game counters
exactly. Initial value predictions are exact by cloning body and retaining head
parameters. The independent critic has fresh moments and step0, separate from
inherited actor Adam. Save both step counters and all eight parameter/moment
arrays; normal loaders must reject old schema. This intentionally resets critic
optimizer history and separates the gradient-norm budgets, so do not claim all
optimizer state is preserved. Both budgets remain0.5; all other PPO settings
stay fixed. A joint-loss backward must not send value gradients into the actor
or policy gradients into the critic.

Before games, test schema rejection, exact actor/value migration, save/resume
of both optimizers, Torch/NumPy inference agreement, gradient isolation and
bounded real train/resume/frozen checks. Independently review the source and
migration. Keep canonical initial and source unchanged during runs.

Train exactly40 Hard games with eight workers from migrated initial bytes,
seed base30000, both maps/all races/five builds,1200 game/300 wall seconds,
cadence1. Compare original eight-worker near-greedy control. Verify initial8
gameplay parity rather than assuming it from seeds. Preserve infrastructure
failures; a pre-game failure may require a whole-schedule repeat, never selective
replacement in training. Record finite returns, optimizer-step changes and
actual critic fit; critic MSE remains a diagnostic rather than strength proof.

Freeze final and evaluate greedy30 on development banks20000 and40000 with
four workers each. Prefer/extend only with at least14 and13 wins respectively.
Otherwise withhold that arm. The reserved final bank50000,70% reliable Hard
acceptance target and richer observation end-state remain unchanged.

The isolated implementation passed90 tests and independent review. Four new
architecture/schema tests failed before the edit; value-only and entropy-only
feedback checks prove both directions of gradient isolation. Resume tests use
different actor/critic step counters. Migration preserves actor parameters,
moments and step676, clones initial critic predictions, and resets critic Adam
to step0/moments0. The migrated checkpoint SHA-256 is
`5b34eb35ab88689f8700d2863626c51290469cedc0965285522028b6c55db65b`.
Across33,556 retained states, logits, values, same-temperature probabilities
and greedy actions match exactly (maximum errors0). These are initial parity
checks, not strength evidence. Actual three-game train/resume/frozen smoke
verification is now running separately from the untouched canonical initial.
Source: `logs/audit/ppo-independent-value-source/`; migration receipt:
`logs/ppo-independent-value/migration.json`; tests/parity receipts:
`logs/audit/independent-value-tests.stdout`,
`logs/audit/independent-value-inference-parity.json`.

All nine actual smoke games completed without failures (three train, three
resume, three frozen), each reaching the120-second cutoff. Resume reached
150 episodes/attempts,692 actor updates and16 critic updates; the inherited
676-step offset is preserved. Frozen sampling leaves checkpoint bytes unchanged.
Both canonical initial files remain untouched. Receipt:
`logs/audit/independent-value-smoke-results.json`. The predeclared40-game
Hard continuation is running from the untouched migrated canonical initial.
