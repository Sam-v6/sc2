# Human production outcome imitation

RL remains off. This experiment changes macro supervision, preserving the broad
raw controller for later integration. Copy a simultaneous vector of own production
outcomes over 45 seconds. Outcomes are not inferred human intentions.

First verify tracker labels: birth/init counted once per tag, starting units
excluded, completion not counted again, mode changes/casualties/captures excluded,
Orbital/Planetary conversion counted once, own research completion deduplicated.
Upgrades completed after the horizon are not labeled even if started within it.
Only verified own tracker chronology supplies targets. Current masked player
observations supply inputs; future events never enter observations.

Use the eleven-game teaching split and the existing three-game development split;
leave reserved games untouched. Initial labels use already verified decision
observations to avoid silently inventing a new observation phase contract. This
is event-sampled rather than uniform-time supervision; report that limitation.
Discard observations without a complete future horizon before replay end.

One fixed nonlinear multi-output regression fit: 128 ExtraTrees, minimum leaf4,
all features, seed8160, two CPU threads, no action history. Predict nonnegative
counts, round to integers for positive-goal metrics. Compare no-production and
teaching-only mean-count baselines. Report per-family precision/recall/count MAE,
macro averages and economy/building/military/upgrade groups. Require better macro
positive F1 and lower macro count MAE than both baselines, and at least0.25
positive precision/recall in building and military groups, before native execution.
No horizon/seed/model sweep if it fails. Stop and diagnose observation/learnability.

If offline gates pass, implement a generic pending ledger and test duplicate
suppression, acknowledgement/rejection, blocked prerequisites, cancellations and
no-goal silence. Executor must not decide worker/supply/expansion/composition goals.
Freeze six bounded native development games (two per race) and explicit scripted
micro, with learned sustained economy and military production required per race.
Native panel does not establish reliable Hard or authorize RL automatically.

Execution ledger: label implementation and chronology audit first; fit/native
work depends on their verified results. CPU-only, approximately80percent host
budget; no download or installation. Prior imitation trial is closed and verified.
