# Diagnose repeated forecast execution

The frozen six-game panel must finish before editing its bound executor. Its first
completed Zerg Rush game reports 54 Depots, despite a one-Depot future-45-second
forecast throughout sampled late states. The executor consumes an observed-order
intent, then immediately admits another from the same standing count forecast.
This is a concrete execution-frequency mismatch. The initial worker/army gains
remain evidence, but sustained-production gates cannot establish good macro alone.

After independent panel verification and source archival, test a bounded cadence
intervention with the same checkpoint/prior and no type-specific caps or recipes.
Track observed successful order consumptions by production family over the model's
1008-loop horizon. Before admitting a new intent, subtract the maximum of recent
fulfilments and current engine queued work from the learned count. Using maximum
avoids charging an observed train order twice as both history and current queue.
Requests already admitted keep their ID/deadline through delays. Failed or unechoed
acknowledgements never count as fulfilment. Expiry rearm still requires a strictly
later positive surplus observation. Record history and effective queue in traces.

This is a rate interpretation diagnostic, not a proof that future-birth predictions
are exact start-time labels. Units/upgrades predict births/completions; building
labels predict starts. Queue/history overlap cannot generally be inferred exactly
from family aggregates, so report this limitation. Do not claim contextual human
imitation or promote RL from the cadence experiment.

Tests must show a standing one-count forecast cannot execute twice in 1008 loops,
a count increase can permit further execution, old fulfilments age out at the
boundary, different families remain independent, rejection/loss/timeout spend no
quota, and queued work/history are not charged twice. Freeze a fresh 600-second
Zerg Rush seed816201 development canary with 240-second wall/80% CPU guard.
Compare replay production with the old Zerg Rush descriptively (different seed);
require Barracks by90seconds, four military births,20livingworkers, and no more
than one observed Depot order per1008-loop window while its forecast is one.
Inspect supply blocks and military production for harm; do not relabel prior failed
or successful engineering gates. Broader fresh all-race tests follow only if useful.
