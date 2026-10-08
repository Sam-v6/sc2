# Training-only history check before recurrent PPO

Freeze this single diagnostic before fitting its predictors. It uses the already
reviewed 80-episode training corpus and retained parent encoder. No evaluation
trajectories, native games, policy updates or checkpoint selection are allowed.
This checks information availability, not gameplay strength.

At each eligible training decision, predict two binary labels eight decisions
later: an observed enemy near the base or army, and an idle barracks or townhall.
Use only logged observations; no hidden-opponent information. Features are the
parent's 64-unit encoding and one-hot previous selected action. Three controls:

- Current encoding/previous action alone.
- Current plus the same features one, four and eight decisions earlier.
- Identical features, with the three past blocks shuffled independently per row;
  current features remain in place. This retains past information but removes
  dependable lag order.

Discard incomplete windows at episode boundaries. Episodes with index divisible
by four are the fixed whole-game held-out set; all others fit the predictors.
Standardization uses fitting rows only. Fit one ridge predictor per control with
penalty1 and an unpenalized intercept, clip predictions to[0,1], and report Brier
errors for both targets plus each held-out episode. No coefficient/lag/horizon
search or repeat with adjusted thresholds.

Support gate: ordered mean error at least2% lower than the current control and
at least0.5% lower than shuffled history, with neither target worse than current.
A failure directs us to revisit this memory mechanism before spending recurrent
native training budget; it does not prove all temporal information useless.
A pass permits implementation of sequence PPO, but cannot establish stronger play.

The CPU-only implementation is `tools/recurrent_memory/history_diagnostic.py`.
Three tests verify causal episode windows, shuffle preservation of past blocks,
and fitting without held-out labels. Bind sources, original corpus, retained
parent and review chain before use, then verify them unchanged afterward. Run
through `tools/low_load.py` with one numerical thread and eight-CPU affinity.
Output is fresh `logs/recurrent-memory/history-diagnostic.json`; do not overwrite
or replace it. No new framework or download is required.
