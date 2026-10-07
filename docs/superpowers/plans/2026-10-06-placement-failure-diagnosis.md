# Diagnose remaining live placement failures

Inventory-native01 is closed as failed, with no promotion or RL restart. Its
verified trace shows 48 Barracks placement blocks and supply demands that cannot
always submit a Depot. These are distinct from human target coverage gaps.
Replay placement queries return generic Error3 even for a site that succeeded
in the live game, so do not use them to choose a geometric repair.

Before a placement repair, retain each live resolve_production_placement trace,
including rejected requests, goal/actor/seed, per-native-result counts and path
checks. Add diagnostics without changing source goal selection or native placement
behavior. Preserve native01's bound snapshot. Freeze a single diagnostic replay
of the existing inventory job with the new logging, 600game/240wall seconds,
same seed/map/opponent/model/library/assistance, CPU-only and80%guard. No fit/RL
or competence promotion. The repeated game is justified only to obtain missing
physical failure evidence; it is not another unchanged policy evaluation.

Classify reserved-space, engine placement result, actor/pathing and budget failures
from that native evidence. If it demonstrates reachable free space near an owned
expansion but not the original seed, fix physical placement coverage without
changing strategic demands. If it demonstrates a different cause, repair that
cause instead. Verify corrected primitives with focused tests and native effects.
Then target human economic/supply recovery examples. Do not alter old gates or
assume current worker-based retrieval produces a coherent winning strategy.
