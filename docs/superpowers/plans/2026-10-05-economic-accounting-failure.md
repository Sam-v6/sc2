# Economic accounting failure

The net-collected-minus-loss objective in the
[short curriculum protocol](2026-10-05-short-economic-curriculum.md) is closed
before training. The first physical capability fixture exposes reward credit
from a refund. It does not pass its accounting gate.

Fixture113000 uses isolated debug setup, never a training or strength game.
After setup, all workers stop. Idle collection/loss counters remain stable.
A normal100-mineral depot payment reduces the bank5050 to4950 with no collected
or loss increment. Canceling that building refunds75, leaving bank5025, while
lost_minerals_economy changes from0 to-75 and collected resources remain0.
Consequently the proposed C-L score increases75 despite a25-mineral net spend.
This is incompatible with the declared unchanged-counter requirement.

The assertion stops at14.1071 game seconds,6.934 wall seconds. Its error receipt,
80 incrementally persisted observations and three checks remain available.
No replay is saved because the assertion exits before the game's replay-saving
step; later morph/mining/destruction stages are untested. This is a semantic
accounting rejection, not evidence that the RL learner failed.

Four synthetic tests and independent source review pass, including a real
subprocess SIGKILL after an observation write. Independent completed-data review
verifies all41 frozen hashes and the raw counter/bank changes. It confirms no
training, checkpoint or curriculum/transfer case use. The three recorded CPU
windows are2.38%,3.65%,5.61%; they are samples, not a sub-window maximum guarantee.

Preserve original `logs/short-economic-curriculum/fixture-source/` and
`fixture-inputs.json` unchanged. Receipt:
`logs/audit/economic-accounting-fixture-complete-independent-review.json`.
No loss-counter clamping, refund correction or hidden reward substitution follows.

A further user-authorized Astra consultation supports the separately declared
[resource-collection task](2026-10-05-resource-collection-curriculum.md). Its
counter validation, data and reviews live in a new root. It remains an auxiliary
task; genuine Hard improvement and final strength acceptance are still required.
