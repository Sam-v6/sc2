# Owned-base construction fallback: verified primitive repair

The human inventory controller requested buildings that its original placement
search could not place. Native diagnostics retained 48Barracks,8EngineeringBay
and7Depot rejected attempts. Main-site native codes were primarily
CantBuildLocationInvalid; Barracks checks sometimes found a legal addon pad but
no legal producer-plus-pad pair. These were placement failures, not worker path
failures. Replay-mode queries returned generic Error3 even for a live-successful
site, so they were excluded from the geometry diagnosis.

Read-only live probes then repeated the failed searches near complete landed own
bases, with the same worker and reservations. All63failed requests had a native
legal reachable fallback near owned expansions. No probe command was issued;
the original controller's production, resource bank and result were unchanged.
The primary diagnosis ran40.29seconds/5.2%peakhostCPU, the probe48.66seconds/7.2%.

The shared construction primitive now first preserves the original search. If
that fails, it searches near complete landed own bases, ordered by proximity to
the original seed. Every fallback retains native placement, addon clearance,
spawn lanes, batch footprints and worker path checks. Enemy/unready/flying bases
are excluded. CommandCenter expansion targets and point-free/addon commands keep
their original semantics. No new strategic demand, worker cap or building quota
was added.

The regression reproduced the missing fallback before the change, then passed.
Full suite508tests/32skips and named-fileRuff pass. Frozen native03 uses the same
inventory policy, seed816201, AcropolisLE/ZergVeryEasyRush,600game/240wall seconds,
CPU-only and80%guard. Independent reconstruction verifies human sources,
deficits/queues/intent transitions, owned base anchors, matching actor/ability,
accepted actions, tracker starts and completion.

| Native metric | Before fallback | After fallback |
| --- | --- | --- |
| Placement failures | 63 | 0 |
| Completed production buildings | 5 | 7 |
| Military births | 41 | 41 |
| Living SCVs | 52 | 52 |
| Final minerals | 3,355 | 2,595 |
| Sampled supply-blocked seconds | 70.36 | 70.71 |
| Result | Tie | Tie |

Four fallback commands were accepted and started: two Barracks, one EngineeringBay
and one SupplyDepot. Both Barracks completed before cutoff; the late Bay/Depot
had started but were unfinished. The declared primitive gate passes. Wall41.30s,
sampled whole-host CPUpeak20.3%, within the ceiling. All three protocols and bound
source snapshots remain in `logs/roadmap/human-placement-native-01/02/03`.

This fixes the demonstrated physical execution failure. It does not repair slow
human worker targets or incompatible addon requests, promote the inventory policy,
revise its failed full mechanism gates, establish useful imitation or unlock RL.
The original 30-game scripted Hard panel remains its historical result. A fresh
three-game regression with this repair won against Terran, Zerg and Protoss Rush
on Acropolis, with zero raw or delayed action errors. Independent replay and
trace reconstruction verifies production, victories and sampled fog-safe combat.
These three games do not repeat the original five-strategy/two-map coverage.
Receipts, replays and bound source are preserved in
`logs/roadmap/primitives-placement-regression-01/panel`.
