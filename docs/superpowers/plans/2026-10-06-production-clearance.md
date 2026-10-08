# Repair generic production clearance

RL off, frozen human model unchanged. Prior six-game panel is closed, with
zero wins and three sustained Macro production passes. Preserve original source
snapshots. This repair changes physical execution, not predicted strategic goals.

Reserve unused addon pads (offset2.5,-0.5,halfwidth1), a one-tile perimeter around
existing/prospective production buildings, and pending/batch construction footprints.
Filter legal building candidates against these reservations, and validate both a
new producer's body and addon pad through native queries. For no-target addon
commands, validate the pad with the SDK's SupplyDepot placement proxy before
issuing. Report blocked pads; do not lift/move existing buildings automatically.
Avoid choosing geysers already targeted by unfinished worker construction orders.

Verify focused geometry/accounting cases and a bounded native debug fixture:
clear Factory starts a TechLab; blocked Factory does not issue its addon; another
building cannot consume reserved addon/spawn space. Debug fixture never counts as
learned competence. Then recheck the unchanged model on the same six Hard jobs
and compare actual replay production, errors and sustained gates. No fit or RL.
CPU-only two threads, approximately80percent whole-host guard, no downloads.
