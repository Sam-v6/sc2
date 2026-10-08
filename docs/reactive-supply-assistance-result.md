# Reactive supply assistance through human production execution

October 7, 2026. A matched native experiment addresses the worker supply stalls
identified in [the queue diagnosis](human-worker-queue-diagnosis.md). This is fixed
professional macro playback plus explicitly scripted assistance, not imitation
training or RL. It uses the same source plan06, map, Zerg VeryEasy opponent and
seed817501 as native22. The30-second instruction deadline remains unchanged.

## Final result

At the exclusive cutoff9224, native25 produces53 SCVs versus45 without assistance;
the human source produces55. Consecutively confirmed worker queue stalls drop
from159.29 to10.00 combined producer-seconds, approximately94 percent less. These
are sums across Command Centers, not elapsed game time. At6000 both native runs
have33 SCV births. At8800 assistance has50 versus45.

Native25 resolves187/247 instructions, versus186/247 without assistance. Both stop
at10552 on the same Cyclone instruction9874 funding deadline. Assistance has90
minerals,133 supply capacity,66 workers and67 army supply at that stop; the control
has85 minerals,117 capacity,54 workers and59 army supply. Worker production and
supply improve; full source execution and useful learned play remain unproved.

Three additional Depot commands are accepted. Independent observations verify
foundations for all three: issued160,7392,10176; foundations248,7424,10208. The first
two finish728,7904. The third remains under construction at the forced exit.
Depots snap their requested half-tile centers to integer centers; verification
checks a unique new nearby Depot rather than asserting exact unsnapped geometry.
All seven delayed supply warnings retain matching zero-progress training orders;
there are no other action errors. Whole-host CPU peaks8.1%, CPU-only.

## What changed

The opt-in job flag `reactive_supply=True` enables an assistance experiment.
Existing callers and the frozen control remain unchanged. The shared need detector
uses the scripted Hard baseline's supply margin and adds paid zero-progress unit
queues to demand. It does not request another Depot while one is under construction
or a worker already has a Depot build order, or at200 supply capacity.

When assistance is needed, unit-training requests preserve100 minerals for a Depot.
The assistance command itself respects the selected macro command's spending and
an overdue zero-food production commitment such as a building or research. It uses
an unbound idle/mining worker, current owned-structure reservations, native placement
and pathing queries. It does not use future human placement or combat outcomes.
Mining and combat do not overwrite that worker's command. Every extra command is
recorded as `reactive_supply_assistance` separately from human tickets.

This changes supply priority explicitly; it is a scripted macro assist. It must not
be reported as learned supply behavior. Broad human commands remain available.

## Earlier matched candidates

| Run | Spending behavior | Result |
| --- | --- | --- |
|22 control|Exact source requests, no extra supply|45 SCV births,159.29 stalled producer-seconds before9224;186/247 resolved|
|23|Extra supply respects only the currently selected command|Two completed extra Depots, but32 births versus33 before6000; stops6968 on Liberator funding,86/247|
|24|Also reserves the oldest overdue request|47 births and105 stalled producer-seconds before9224; only the opening extra Depot; stops9224 on Cyclone funding,148/247|
|25|Save Depot minerals before further training; preserve zero-food commitments|53 births and10 stalled producer-seconds before9224;187/247, same later funding stop as22|

The failed candidates remain frozen with code snapshots and receipts. Reduced
supply warnings or accepted commands alone were not used to declare improvement.

## Evidence and next action

Receipts and replay traces are in `logs/roadmap/fixed-human-plan-native-23/24/25`.
Each has `contract.json`, `report.json`, `episode/`, `source-snapshot/` and
`verification.json`. Independent verifiers bind archived code, original source
plan, shared replay seeds, actual Depot foundations/completions and matched cutoff
tracker births. Source22 remains frozen. Full suite551 tests with32 optional skips,
Ruff and whitespace checks pass.

Use this verified supply behavior in the next explicitly declared human-imitation
execution experiment. Keep supply learning as a later responsibility to transfer
back to the policy once current-state inputs and human targets support it. Inspect
remaining mineral allocation and production queues before fitting or restarting
RL. The learned full-game, micro-transfer, all-race Hard and higher-difficulty
requirements remain open; the separately verified scripted Hard baseline is intact.
