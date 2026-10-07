# Human-supervised production timing experiment

RL remains off. First audit is `production-timing-audit-01`: original human labels
verify against saved count vectors; native opportunities are descriptive proxies,
not proof of native castability or a causal diagnosis. No new simulation/fit yet.

For each52goal family, supervise whether its outcome occurs within45seconds and
the normalized time to its first outcome multiplied by that presence indicator.
Absent goals have zero presence/time mass. A shared regressor's time-mass divided
by presence estimates conditional timing; zero predicted presence means unknown,
not a fabricated zero-second deadline. These are outcome times, not human command
intentions. Future events are exclusively targets.

Keep the passing count model frozen. Fit one separate104-output ExtraTrees model
on the exact same5,378teaching rows/current-state inputs; no history, no reserved
use.128trees, leaf4, all features, seed8161, two CPU threads. Normalize each output
by teaching-only standard deviation floor0.1. Maximum600fit seconds, total900;
no horizon/seed/weight sweep. Use976previously used development rows for diagnosis.

Evaluate conditional first-outcome timing only on actual positive goals, per family
and grouped economy/building/military/upgrade. Compare teaching-only family median
and45/2constant baselines. Require macro family timing MAE lower than both, at least
95percent timing coverage among the frozen count model's positive predictions,
and no group worse than the family-median baseline by more than2seconds. Verify
labels by an independent scan and reload predictions/metrics before live use.
These gates cannot prove macro competence or unlock RL.

If offline checks pass, replace the unlearned last-served resource priority with
learned outcome urgency. Birth/research/conversion outcomes require distinguishing
work already queued and production duration; construction labels mean starts.
Freeze exact scheduling/accounting rules before code: deadlines must not reset
endlessly on replan or cause repeated construction requests. Native pending and
completed work remain separate; missing timing is explicit. Do not insert worker,
supply, army or prerequisite goals. Then one same-job bounded native comparison,
with unchanged counts, observations, placement and combat assistance. No RL.

A timing failure does not establish the cause of poor native behavior. Stop this
variant and investigate supervised learnability/observation/state-distribution;
do not repeat unchanged fits or substitute scripted macro priorities as success.
