# Combat event reward experiment

Direct Hard40 finite-win learning produced no training wins and the control
subsequently lost all six greedy and all six sampled frozen games. Full-return
potential shaping cancels: without wins, return targets contain the state
potential offset but no action-dependent successful-outcome signal. The trained
greedy control did not select production buildings. More exploration alone
has not established improvement.

The earlier combat-credit experiment added kill totals to a potential. This
experiment instead proposes actual counter increments as non-potential rewards.
That changes the objective and may favor combat or defensive trades over winning;
therefore keep it an explicit experiment and judge only real game victories.

1. Use archived finite/spatial initial actor, not failed Hard40 continuations.
   Keep observations/actions/micro/temperature 1/finite terminal convention and
   lambda 1 fixed. Retain the frozen initial greedy/sampled baselines.
2. Add `combat-events-v1`: each macro transition receives
   (increment killed unit + structure value - increment own lost mineral and
   vespene value) / 100 in unscaled reward, alongside the existing potential
   difference and true-win 100 payoff. Unchanged counters give zero event reward.
   Initialize previous counters at the first decision so pre-policy events are
   not attributed to an action. Record all components, including the final
   observed counter increment; do not fabricate unobserved terminal events.
3. Add tests for positive kills, negative losses, no recurring credit, correct
   transition attribution and finite terminal treatment. Check NumPy/Torch
   reward-context rejection. Explicitly migrate actor only with critic and Adam
   reset, recording source/parent/output hashes; no rollouts are carried forward.
4. Controlled engine evidence: combat-event-score-probe created Marines and
   weakened visible enemy units solely to validate counters. It recorded 132
   observations: killed units 150 to 950, structures 0 to 500, own loss value 0
   to 300; every counter was nondecreasing. This is a score API fixture, never
   training data or playing-strength evidence. Preserve its replay and JSON.
5. Separate train/resume/frozen smoke from untouched initial weights. Start a
   bounded Easy curriculum to obtain varied actual trades, then freeze both
   greedy and sampled development evaluations. Scale training only when receipts
   show valid event components and useful action exposure. Do not broaden to the
   reserved acceptance bank on weak development performance.

No event reward code or trained event policy has been implemented yet. The
reliable Hard win-rate goal remains open.
