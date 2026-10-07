# Learned production choices through native primitives

The resource-only offline inference checks passed. One frozen native canary then
tested the unchanged fit04 production head through the existing broad adapter,
with scripted actor selection, placement, fixed44-loop cadence and8-loop retries.
Mining, gas, reactive supply, worker scouting, army destinations and combat micro
remain separately attributed assistance. No worker, military or production-building
quota replaces model decisions. No training or RL occurred.

The model uses the existing explicit partial-observation projection with human
command history cleared. Execution retains complete native observations. Select
the highest-probability funded ability with a currently available owned actor.
Unknown prices are withheld from native issuance instead of guessed. Native
availability is an additional execution guard; the offline source lacked those
queries. An accepted request waits for an observed order or building foundation.

Contract: AcropolisLE, VeryEasy Zerg Macro, seed824101,600game-second cutoff,
180wall-second cap,80% whole-host CPU guard. Gates require8new workers,20military
units,2completed production buildings, zero action errors and normal completion.
This is a limited conditional-choice canary, not broad raw-action imitation,
learned timing, Hard competence or a professional strategy claim.

## Verified failure and concrete execution defect

`logs/roadmap/professional-choice-native-01/verification.json` has status
`verified_failed_native_choice_canary`. An independent verifier reconstructs all
788 model probability vectors and resource-filtered sets from native observations
and the bound projection. Each selected ability is the highest-probability eligible
one; commanded actors have native-query ability availability. All72 production
submissions have immediate Success acknowledgements.

Chronological native traces show25new own SCV identities and8completed production
buildings: one Barracks, five Factories and two Starports. Fifteen new observed
military identities are six Marines, one Reaper and eight Hellions. Six MULE
identities are excluded from military counts. A Liberator command is accepted but
its birth is not observed before the abort. These are trace observations, not
independently decoded replay births. There is no completed game replay or victory
because the callback aborts.

At loop10565 the model requests a Depot with SCV4348182529 at(39,127.5). The engine
echoes its construction order at(39,128), but no nearby foundation appears. At
loop10684 the engine reports delayed ActionResult44, `CantBuildLocationInvalid`,
for that same actor and ability319. The worker later resumes mining. The wrapper
does not handle the delayed failure; its global pending request blocks further
production and eventually raises after448loops, ending at loop11014. Last recorded
loop11013 is approximately491.7game seconds. Total wall69.0seconds; sampled host
CPU peak6.4%.

The prototype has additional identified execution limitations: it passes empty
spacing reservations to production placement and expires builder protection after
44loops even when no foundation has appeared. Many workers and structures occupy
the surrounding area. That does not prove which occupancy or coordinate issue
caused the engine's placement failure; the delayed error itself is verified.

The last player observation has37workers, zero idle workers,1,385minerals,
1,256gas and15army units. This establishes working economy and some learned
production, while exposing overconstruction and insufficient army output. The
military gate, action-error gate and normal-completion gate fail. Do not attribute
all weak macro to the execution defect or promote the controller.

## Next repair and artifacts

Repair accepted-request follow-through before another game: consume delayed engine
errors, retain builder protection until an observed foundation or explicit request
failure, supply physical production-space reservations, and requery a legal site
for the same construction intent after a recoverable placement failure. Do not
silently replace a failed learned building decision with scripted army production.
Bound retries and retain every failure. Test against captured failed observations
before changing the executor. Also verify grid alignment against actual engine
behavior rather than assuming a successful placement query proves an eventual
foundation. Only then rerun a fresh canary with declared changes.

Prototype runner: `logs/roadmap/run_professional_choice_native_01.py`.
Verifier: `logs/roadmap/verify_professional_choice_native_01.py`.
Contract/report/source snapshots, native static data and compressed trace are under
`logs/roadmap/professional-choice-native-01/`. The adapter loads an older GoalFirst
checkpoint for its engine vocabulary, but the runner overrides its decision method
and reconstructs decisions from fit04's separate choice NPZ. The inherited adapter
controller label is therefore not proof of which checkpoint made the decisions;
use the bound runner, decision vectors and verifier for provenance.

## Construction repairs and completed rerun

`ProductionRequest` now distinguishes immediate acknowledgements from visible
effects, consumes matching delayed errors, retains the original geyser position,
does not count existing structures as new effects, and recognizes addons before
their attachment tag appears. Native execution keeps pending builders protected,
uses physical spacing reservations and bounded same-intent placement retries.
Placement queries and commands now use building-footprint grid centers. The
prototype chooses the shortest queried builder route and adds its conservative
movement-time allowance to the20-second timeout rather than timing out a still
walking SCV. Model weights and macro priorities are unchanged.

Two intervening runs remain preserved: native02 timed out on a visibly constructing
Reactor with no attachment tag yet; native03 passed that case but timed out on a
still-walking Barracks builder. Their traces supplied regression cases. Seven
request-tracker tests and a grid-center regression test were observed failing
before their corresponding repairs. The full default suite passes595tests with
40optional skips; focused tests, Ruff and diff checks pass.

`logs/roadmap/professional-choice-native-04/verification.json` independently
reconstructs911 prediction vectors,87 accepted commands, pending statuses,
547 protected-pending frames, nearest-builder choices and route-time budgets.
Replay tracker decoding confirms28SCV births,16military births (11Marines,
one Reaper, two Mines, two Medivacs; seven MULEs excluded), and8completed Barracks/
Factories/Starports. Immediate and delayed action errors are zero. No retry is
needed. The game reaches its600-second cutoff normally and saves a replay,
ending in a Tie. Wall56.6seconds, sampled whole-host CPU peak24.1%, including
concurrent regression testing. The military gate remains20and fails; all other
canary gates pass. Status stays `verified_failed_native_choice_canary`, not a
victory, Hard competence or RL readiness claim.

The last observation has40workers, zero idle workers,1,640minerals,940gas and
16army units. Requested construction remains excessive:17Depots,7Bunkers and
9Starports. Do not infer all this is a bad model preference: the read-only
`busy-producer-audit.json` finds17building selections where a higher-probability
funded training ability was present in the native availability query, but the
executor rejected its busy producer. Those preferred choices were9Marines,
6SCVs, one Reaper and one Medivac. This is a concrete consequence of the current
idle-only actor rule; it does not prove a queue change will win games.

Next test bounded native training queues, retaining native resource/supply
availability and preventing unlimited queue flooding. Preserve default behavior
for unrelated controllers, declare the new canary setting and independently
verify resulting training orders and births. Inspect any remaining model issue
after correcting this executor restriction; do not retrain around it or lower
the military gate. Human broad-control competence, learned micro and RL remain
open. Runner/verifier04 and their frozen contract, source snapshots, trace and
completed replay remain under `logs/roadmap/`.

## Bounded training queues: native 05

The idle-only executor restriction is repaired as an explicit opt-in:
`eligible_actors(..., max_train_orders=2)` permits one waiting training order
behind an active training order, only with native ability availability. Busy
research, construction and morph commands remain excluded; existing callers
retain the one-order default. The canary explicitly queues busy-producer Train
commands. `ProductionRequest` compares the matching order count before and after
issuance, so an old order cannot acknowledge a newly requested queue entry.

The matched native 05 run used the same model, map, opponent, seed and cutoff,
with no training or RL. It reached the normal 600-second Tie cutoff, saved its
replay, and independently verified 948 probability vectors, 89 accepted commands,
498 protected pending frames and zero action errors. Replay decoding confirms
26 new SCVs, 17 military births and 15 completed production buildings. The frozen
20-unit military gate still fails. Wall time was 54.508 seconds and sampled
whole-host CPU peaked at 7.2 percent.

`logs/roadmap/professional-choice-native-05/queue-building-audit.json` verifies
all 27 queued commands changed the requested producer from one observed order
to two on the following observation. Of 40 building commands, 32 ranked above
at least one funded, native-available training action even with bounded queues;
eight had no eligible funded training action. The remaining overbuilding cannot
be attributed solely to the repaired idle-only restriction. Many completed
producers were idle at cutoff, with 1,160 minerals and 1,050 gas available. This
is a decision-quality issue to investigate separately from primitive execution.
Do not impose an undisclosed unit quota or count this as learned competence.

Regression tests were observed failing before implementation. All 598 default
tests pass with 40 optional skips; focused production tests, Ruff and diff
whitespace checks pass. Next inspect the remaining unit-production constraints
and offensive/micro effects before deciding which learning changes are warranted.
