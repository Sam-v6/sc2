# Primitives reset: loss evidence and reference code

Training is paused. The next controller is a scripted execution baseline, followed
by professional imitation using its verified primitives, then reinforcement
learning. None of the reference work below establishes learned game strength.

## What the saved losses show

The repaired six-game human-outcome panel had three Rush defeats and three
ten-minute Macro cutoffs. The audit at
`logs/roadmap/primitives-reference-01/loss-audit.json` binds the six saved traces,
native catalogues and episode receipts. Reproduce it with
`PYTHONPATH=. .venv/bin/python logs/roadmap/audit_primitives_losses_01.py`.

After two minutes, mining-order presence accounts for 91.5–93.6 percent of sampled
SCV observations; idle workers account for 0.36–0.75 percent. Samples are roughly
2.14 seconds apart. Orders alone do not prove income, travel efficiency or safety.
This evidence does not support widespread idle workers as the dominant failure.

Macro games reach 88/126/132 spare supply and 3,453/3,313/3,441 gas while median
minerals are only 70/70/75 after two minutes. Supply blocking is absent in these
Macro samples. The controller constructs excess supply, banks gas, and maintains
too little mineral-funded production. Earlier timing diagnostics also found
affordable idle worker-production opportunities. Availability queries were not
saved, so those opportunities remain a proxy rather than proof of castability.

Source inspection confirms two concrete execution limitations:

- `ProductionGoalBot.assistance` attacks visible enemy units, with no attack-move
  destination, offensive rally or search for enemy bases. All recorded assistance
  attack commands in these six traces target units; none target a position.
- The production scheduler stops considering all subsequent goals when its first
  eligible request is unaffordable. Future outcomes are treated as immediate work,
  with oldest-request priority. This can reserve resources ahead of cheap workers
  and military units. It is a plausible contributor, not an isolated causal result.

The previous native panel already proved addon placement repairs: actual Factory
TechLab starts in six of six games and no delayed action errors. More placement
patches alone are unlikely to resolve the missing offense and economic balance.

## Reference selection

Use [Sharpy](https://github.com/DrInfy/sharpy-sc2) as the primary design reference
and [Burny's examples](https://github.com/BurnySc2/python-sc2/tree/develop/examples/terran)
as small executable comparisons. Both use the Python SC2 interface already in this
project. This is a compatibility choice, not a claim that either is currently the
highest-ranked bot. [Sharky](https://github.com/sharknice/Sharky) is an additional
C# reference; adopting its complete runtime would add unnecessary setup here.

Saved source manifest:
`logs/roadmap/primitives-reference-01/sources/manifest.json`.
Sharpy revision: `d9577a00ee47634b56ff7ee0740c6ed3043659a2`.
Burny revision: `81d66110cb0aa57cc7c2895dad207775e496fbd1`.
Only selected small source files and tree metadata were downloaded, without
installing a framework. Both inspected source repositories carry MIT licenses;
retain the applicable notices for copied or substantially adapted code.

| Primitive | Inspected reference | Apply here |
|---|---|---|
| Worker distribution | Sharpy `distribute_workers.py`; Burny `mass_reaper.py` | Protect builders, saturate useful bases, move workers off excess gas and depleted resources |
| Construction follow-through | Sharpy `terran/continue_building.py` | Resume unfinished Terran buildings when their builder is lost |
| Repairs | Sharpy `terran/repair.py` | Assign a bounded set of safe workers to useful repairs |
| Army gathering and offense | Sharpy `zone_attack.py`, `marine_rush.py` | Gather forces, select an attack destination, reinforce and search after clearing a base |
| Mobile micro | Burny `mass_reaper.py` | Attack compatible visible targets, retreat when hurt, move during weapon cooldown, respect pathing |
| Bio and tank abilities | Sharpy `micro_bio.py`, `micro_tanks.py` | Gate stim by research, health and combat; siege/unsiege based on nearby visible ground threats |

Sharpy's Marine Rush plan also explicitly schedules worker scouting, MULEs,
depot lowering, defense, repairs and interrupted construction. Its named tactics
identify gaps in our execution layer; copying the whole framework is unnecessary.
Inspect its shared micro/pathing code before implementing behavior that depends
on those helpers.

## Native comparison and next implementation

An unchanged local `MassReaperBot` lost a bounded Hard Zerg Rush canary at 752.5
game seconds, taking 36.9 wall seconds. This is scripted evidence only. The
instrumented six-game comparison uses AcropolisLE, Hard Rush and Macro per race,
seeds 817101–817106, step eight, a 1,200-second game limit, 300-second wall limit,
sequential games, and cancellation after three sampled host CPU readings above
80 percent. Its source bindings, telemetry and replays live under
`logs/roadmap/primitives-reference-01/panel`. Engine seeds are fixed; the reference
bot's Python random choices were not seeded by this diagnostic harness. Do not
present this as a fully deterministic reproduction or final acceptance panel.

The panel is now terminal: six defeats, zero cutoffs or victories, and sampled
whole-host CPU peak 64.2 percent. Each game peaks at 21 workers and only 7–11
Reapers. Engine score telemetry reports zero killed structure value in all six
games. Source hashes were rechecked and replay sizes/hashes recorded in
`panel/summary.json`. This establishes that the existing harassment example is
not a sufficient Hard baseline here; it does not establish the cause of every
loss or evaluate Sharpy itself.

Build a modest Terran baseline with an economy that can fund sustained production
and a composition capable of hitting ground and air opponents. Keep primitive
execution separate from the declared scripted build and attack choices, so human
imitation can later supply those decisions. Verify mining income, continued
construction, worker and military births, attack destinations, combat abilities
and actual outcomes in native games. First run bounded diagnostic games, repair
observed failures, then freeze the 30-game all-race Hard evaluation. Include
defeats, timeouts and per-race results. Do not train another model while these
basic execution requirements remain unresolved.
