# Recovering human repeated commands

October 7, 2026. The importer previously read only `SCmdEvent`, omitting target
updates and command-manager repetitions. A new source-event expander retains the
original ability, queue flags, target and manager sequence with explicit provenance.
It excludes contexts after selection/control-group changes, unknown manager states,
and target updates without a manager at the same loop. Those unresolved manager
slots now appear as unknown history, preventing false next-action timing labels.

The reader's own source documents command-manager events as repeated player
commands, including repeated worker training; see
[sc2reader game events](https://github.com/ggtracker/sc2reader/blob/upstream/sc2reader/events/game.py).
That description alone is insufficient for teaching labels. Every newly accepted
label additionally matches a mutually unique converted action, a selected full-tag
owned actor, an independently named ability/index and the precise original target.
Actor types are checked against the source record and causal original tracker.
No label is invented from an eventual unit birth.

The fresh recovery preserves all851 existing commands and adds305 verified labels:
139 Smart,107 Attack,34 Hellion training,4 SCV training,3 Factory builds,3 Cancel Last,
7 Cyclone training,1 Refinery build,2 Depot builds,2 Widow Mine training,
2 Liberator training and1 Marauder training. These counts cover the full source
game, not only its first600seconds. The missing Factory placement at7171/637
resolves to SCV4357619713 and point(134.5,37.5), matching its converted action.

The teaching game was reimported with1156 labels. Independent verification preserves
all851 old labels and their player/unit/map/memory observations. Command history now
includes recovered repetitions and399 unknown repeat contexts; provenance stays
outside observations. The importer still declares missing fields, partial human
observations and an original engine version unavailable locally. This is improved
teaching data, not a new fitted model, useful imitation or game-strength evidence.

## Fixed-plan integration

The first expanded plan has241 instructions within600seconds:29 more macro
instructions and the same9 builder movements. It preserves all212 previous
instructions. Native14 stopped at a supply deadline: the worker's Depot command
never created its foundation before a later move interrupted it. The source human
had moved that worker away from earlier Starport construction; the compiler had
incorrectly filtered those two distant moves out.

Plan05 retains those movements, giving243 instructions with11 builder movements.
Moves near the next build site keep the worker reserved; moves away from a building
allow mining assistance after arrival. Native15 recovers the missing Depot and
raises supply capacity54→62, but a later Depot misses a worker-production deadline.
Native16 skips futile supply-blocked production probes, improving that Depot's
submission6528→6520; the game still stops at7008. Trace inspection finds that a
50-mineral reservation for an earlier supply-blocked SCV delayed the100-mineral
Depot. The reservation rule now excludes supply-blocked requests; native17 is the
matched follow-up, preserving seed, plan, game step and deadlines. It resolves82/243 but still stalls on Liberator availability.

Source artifacts and independent checks:

- `logs/roadmap/human-command-repeats-01/verification.json`
- `logs/roadmap/human-command-repeats-01/corpus-verification.json`
- `logs/roadmap/fixed-human-production-plan-04/plan.json`
- `logs/roadmap/fixed-human-production-plan-05/plan.json`

RL and imitation fitting remain paused until native execution is useful. Full
command coverage still needs work:399 contexts are explicitly unresolved, and
only the existing single winning game's new labels were recovered in this pass.

## Verified queue admission and the latest native result

Two isolated native fixtures create a Starport and fill supply15/15, then issue
Liberator training626. The normal ability query omits626; the same query ignoring
resource requirements includes it. Both commands are accepted, paid, and retained
at zero progress. After debug removal of three Marines frees supply, the order
progresses and produces a Liberator at1192 without another command. Both have zero
action errors, correct replay seed820001, bound source snapshots and independent
verification. Debug setup isolates admission semantics, not game strength. Their
reused supervisor wrapper marks reports failed because it expects the fixed-plan
status vocabulary; the fixture receipts and traces are completed. Original reports
are preserved, and verifiers state that limitation explicitly.

Fixed-plan training queries now ignore resource requirements, with mineral/gas
prices still checked explicitly and technology prerequisites still queried.
NotEnoughFood warnings are distinguished from lost instructions only when the
same owned producer retains a matching zero-progress training order. The warnings
remain in traces and history; they are not reported as zero action errors.
Native18 resolves88/243, then exposes another supply guard defect: queued demand
made free supply negative, blocking even zero-supply buildings. Native19 corrects
that and resolves138/243 before another Factory landing failure. It creates the
previously missing Factory from the recovered7171 command. Landing clearance had
allowed combat assistance to send units back after they left the footprint, and
some escape points overlapped neighboring buildings.

The primitive now avoids visible owned ground structures and keeps cleared units
held outside until landing ends. Native20 independently verifies that the recovered
Factory attaches to the Tech Lab at(134,41), first at8624. It resolves148/243 and
stops at9224 on a Cyclone request with only60minerals available. All eight recorded
supply warnings retain matching queued orders; there are no other action errors.
CPU peaks9.2%. The stop is a forced diagnostic leave, not a natural loss.

At9224 the native observation contains41 living SCVs,3 MULEs and reported army
supply45. The nearest source frame9196 contains50 living SCVs,5 MULEs and reported
army supply29. These differences mean income, production queues and combat losses
must be compared before blaming another execution primitive or fitting a policy.
The source fights a professional opponent while this diagnostic uses VeryEasy and
scripted combat assistance; absolute replay timing is not an adaptive strategy.

Next audit worker training and the399 unresolved manager contexts against original
selection state, plus resource income, queued commitments and source/native combat
attrition. Keep the source observations intact. Do not relax the existing deadlines
or restart an unchanged fit to hide the mismatch. Then rerun the fixed-plan gate
and move to useful observation-conditioned imitation through these primitives.

The updated module regressions, whole suite548tests/32skips, Ruff and whitespace
checks pass. Further verification is in native14–20 `verification.json` files and
`supply-queue-fixture-01/02/verification.json`. No model was fitted or RL resumed.
