# Human production forecast diagnostic

Frozen before fitting. Current phase remains supervised human imitation, with RL disabled.

Use repaired teaching games 294,870,955,839,991,523 and previously used development games 887,920,851. Reserved replays remain untouched. Verify dataset source bindings before loading. Label the next retained Build/Train/Research command, also including Morph abilities that produce an engine Structure (attribute 8). Censor intervening unresolved events. Independently reconstruct each label with a forward scan. Future abilities and delays are targets only; no future observations, human selection, actor labels or target labels enter features.

Fit two closed-form ridge diagnostics: masked current state plus current own type/status, and that same state plus chronological causal human history. Teaching-only RMS scaling, active columns and classes; fixed regularization 0.1. Fit native ability one-hot scores and log1p delay in seconds jointly. This diagnostic is not a game controller and does not restrict the final raw action space. Repeated forecasts of the same event are not independent demonstrations.

Report teaching/development accuracy, class macro recall, per-class counts and delay MAE, including strictly positive delay rows separately. Compare against teaching-majority ability and teaching-mean delay. Require solved-system relative residual below 1e-8; this validates the numerical solve only. No sweep, promotion, native trial or RL follows automatically. Findings choose the next controller change.

Use existing CPU Python/NumPy/SciPy, two BLAS threads, no GPU. Total execution bound 600 seconds; stop after three whole-host CPU samples above 80 percent. Save feature matrices, labels, predictions, models without pickle, source/code/plan hashes and telemetry. Independently reload artifacts and reconstruct predictions and metrics before reporting conclusions.
