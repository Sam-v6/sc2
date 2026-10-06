# Assisted human-outcome native development result

October 6, 2026. Frozen human imitation now drives actual production in full
native games. Six Hard development games completed and independently verified:
zero victories, three Rush defeats and three ten-minute Macro cutoffs. The full
all-race useful-start gate fails. RL remains off; this is not roadmap completion.

The120-second VeryEasy engineering canary completed56planning frames, no action
errors, and actual Depot/Refinery/Barracks/CommandCenter/Factory production plus
four new workers. Its acknowledgements and all predictions independently reproduce.
It is engineering evidence only. Peak whole-host CPU14.2percent.

The live input path exactly reproduces all976saved human development feature
rows after applying the professional missing-field/order-alias profile and removing
history. Richer native data serves execution only. Current-state masked inputs,
model parameters and all six development jobs were frozen before the panel.
Planning requested44loops and sampled every48loops because game_step8 rounds
up the requested interval; report actual cadence rather than claiming exact44.

| Hard opponent | Result | Peak workers | Peak live military | Useful-start gate |
|---|---|---:|---:|---|
| Terran Rush | Defeat455s | 22 | 6 | Fail |
| Terran Macro | Cutoff600s | 40 | 27 | Pass |
| Zerg Rush | Defeat533s | 22 | 7 | Fail |
| Zerg Macro | Cutoff600s | 49 | 28 | Pass |
| Protoss Rush | Defeat509s | 22 | 4 | Fail |
| Protoss Macro | Cutoff600s | 48 | 29 | Pass |

Worker peaks use the native food_workers field to include workers temporarily
inside resource structures. Gates require concurrent30workers/8military/complete
Barracks and sustained actual births in both declared time windows. Cutoffs are
production evidence, never wins. The three Macro games produced28/41/40newSCVs
and28/32/32newmilitary units respectively. These are replay tracker births,
not acknowledgement counts. Broad raw control and learned micro remain incomplete.

Independent verification reconstructs1,543native model predictions, goal-linked
commands and acknowledgement counts, and reads original replay tracker events for
actual production and time-window gates. Engine source snapshots are preserved
before subsequent fixes. Receipt:
`logs/roadmap/human-goal-native-01/panel/verification.json`.
Panel peak whole-host CPU27.2percent, sequential CPU-only games, no fit/RL.
All action acknowledgements were successful, but one delayed native action error
was CantFindPlacementLocation for a Hellion spawn in Terran Macro. Successful
acknowledgements do not prove construction/production actually occurred.

Diagnosed execution fault: shared native addon aliases let a Factory Tech Lab
goal choose a Starport caster. Trace at loop5952inZergMacro shows precisely that
mismatch. A failing unit test reproduces it; eligibility now restricts addon
families to their corresponding grounded production building. This fix is tested
but has not yet been rerun natively. Existing sources/results remain archived.

Unresolved execution issues: no-target addon requests on some actual Factories
were acknowledged but never became orders/foundations, suggesting blocked addon
clearance; a delayed Hellion spawn failed placement. Investigate these through
bounded physical fixtures and preserve addon/spawn clearance in generic placement.
Do not silently lift/relocate structures or add strategic prerequisites. Also
trace acknowledged-but-unstarted Refineries before treating their counts as fulfilled.

Assistance remains explicit: legal placement near the base/resource-cluster
expansion placement, idle minerals and existing-refinery saturation, visible-contact
combat, and least-recently-served resource fairness. No scripted build/train goals
or attack timing were inserted. This is an assisted macro imitation experiment,
not the final unrestricted human-command controller or learned combat policy.

Tests: focused input masking/history invariance, addon alias and queued foundation
accounting pass. One existing descendant-timeout test failed while native games
were active; it passed in isolation and the full415-test suite passed once games
stopped (31optional skips). No runtime cleanup code was changed on that evidence.
The final416-test suite passes with31optional skips and includes the new alias
regression. Do not erase the earlier
failure or claim its root cause proven.
