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
requires separating model ranking from affordability and availability fallback;
it does not by itself prove the raw model prefers these buildings.
Do not impose an undisclosed unit quota or count this as learned competence.

Regression tests were observed failing before implementation. All 598 default
tests pass with 40 optional skips; focused production tests, Ruff and diff
whitespace checks pass. Next inspect the remaining unit-production constraints
and offensive/micro effects before deciding which learning changes are warranted.

## Concurrent execution diagnosis: native 06 and 07

A hash-bound `serial-attack-audit.json` under native 05 records 498 globally
blocked pending frames, spanning 3,984 loops (177.9 game seconds). After 120
seconds, 4,700 of 5,765 completed-producer observations have no orders; these
are sampled observations rather than exact utilization durations. Maximum ground
combat supply is 20, below the declared scripted offensive start threshold of 40.
This canary therefore does not demonstrate an offensive campaign or combat micro.

Native 06 tested actor-keyed concurrent pending requests, but stopped with a
false timeout. At loop 4348, the requested CommandCenter's existing SCV order
has progress 0.97794116; at loop 4356 the newly queued order has progress
0.011029422, still one order. The count-only tracker misses this rollover.
Its failed receipt, trace and source snapshot remain preserved. Code inspection
also identified inherited `learned_control` clearing on new commands; the
concurrent wrapper now unions all pending actors before primitive assistance.

The tested tracker repair accepts a progress rollover only for an explicitly
queued command with exactly one pre-existing matching order. Two existing orders
cannot acknowledge a third through rollover alone. The regression was observed
failing before implementation. All 599 default tests pass (40 optional skips);
Ruff and whitespace checks pass.

Native 07 completes the matched 600-second Tie cutoff with zero action errors,
a replay and independently recomputed 1,172 prediction vectors. The verifier
checks 675 protected pending actor observations and 45 selections while another
request remains pending, excluding pending actors from new commands. The wrapper
also reserves all pending construction footprints and producer addon space.
It permits one prepared command per existing 44-loop decision cadence; no
model fitting, unit quota or RL is added. Wall time is 83.816 seconds; sampled
whole-host CPU peak is 23.4 percent.

Replay events confirm 50 SCV births, 12 military births (nine Marines and three
Reapers), and one completed production building. The controller submits 37
Bunker commands. Both the frozen military and production-building gates fail.
The final player has 62 workers, 5,200 minerals, 1,406 gas, and 12 military units.
Concurrent execution works, but the filtered decoder produces worse
strategic behavior in the changed trajectory. A subsequent audit below identifies
why attributing all Bunkers to the raw model was too broad. Do not describe this as an
imitation improvement or impose a hidden military quota to pass the gate.

The next decision is the imitation formulation, informed by this loss evidence.
Keep the known scripted Hard baseline separate. Consult the existing authorized
Astra adviser rather than repeat closed memory, weighting or epoch sweeps. The
actor-keyed concurrent wrapper remains an experimental diagnostic runner in
`logs/roadmap/run_professional_choice_native_07.py`, bound and preserved with its
source snapshot; it is not a claim of integrated full-game learned control.

## Corrected attribution: funded fallback starves preferred capacity

Independent parent and Astra audits agree: **none of the 37 accepted Bunkers in
native 07 was the model's global highest-probability choice**. Its raw preferred
action was Factory in 27 cases, Starport in nine, and Barracks in one. Each was
unaffordable and removed by the decoder. The trace-bound
`funded-fallback-audit.json` preserves every source loop and probability. At loop
5344, with 100 minerals and 654 gas, Factory probability is 0.7915937304496765
and Bunker probability 0.02503737434744835. Their native costs are (150,100)
and (100,0). Buying the Bunker spends the minerals needed to reach the preferred
Factory's price. This supports a decoder-induced savings-starvation mechanism,
not a proof that the model's unfiltered strategic choices are competent.

The frozen comparison contract is
`logs/roadmap/resource-reserved-intent-comparison-01/contract.json`. Native 08
reproduces the fallback arm with resource-ignoring availability queries recorded;
native 09 retains a priced, technically available model intent, waits rather than
substituting cheaper work, and reserves pending costs until start acknowledgment.
Reactive supply respects the reservation. Mining, scouting and combat continue;
construction completion does not globally block other actors. An unexplained
unissued-intent stall beyond 60 game seconds aborts. No fits, RL, quota, cadence
or temperature sweeps follow this matched pair automatically.

Before native 09, the query prerequisite independently passes: 285 observations
expose an underfunded but technically available Factory only in the resource-
ignoring query; 391 observations exclude Factory before Barracks completion;
1,172 exclude Starport without a completed Factory. The fallback arm again
records 37 Bunkers, 12 military births, one completed producer, zero errors and
the normal 600-second Tie cutoff. The gate stays failed.

Regression tests first fail for the captured Factory/Bunker spending case,
unknown preferred prices, and pending cost reservations. All 602 default tests
pass with 40 optional skips; Ruff and whitespace checks pass. This is a decoder
experiment, not learned timing or broad human imitation.

### Pair closed: occupied gas target blocks reserved arm

Native 09 stops at the frozen 60-game-second unissued-intent limit. Independent
verification recomputes 473 prediction vectors, all reservation budgets and
intent transitions: 18 intents created, 17 submitted, zero invalidations, zero
action errors. The eighteenth is BuildRefinery, created at loop 3044, still
unsubmitted at last logged loop 4388. Its target is neutral geyser 4323278849
at (26.5,135.5), but owned completed Refinery 4352114690 occupies the same
position. Native placement queries repeatedly reject it with result 42. No
accepted action or completed game follows; the error receipt and source snapshots
are preserved. Wall time is 18.491 seconds, host CPU peak 6.4 percent.

`claimed_geysers` previously accounted only for worker construction orders,
missing completed gas buildings while their neutral geyser remains observed.
A regression using the exact captured tags, positions and contents fails before
the fix. The helper now excludes neutral geysers occupied by an owned gas
building as well as those claimed by pending orders. All 603 default tests pass
with 40 optional skips, and Ruff/diff checks pass. This helper is shared with
`production_goal_play.py`; the failed run itself is unchanged.

The canary also limits gas sites to within 15 tiles of the initial start. At
stall it has completed town halls at (33.5,138.5) and (31.5,113.5), with observed
free expansion geysers at (28.5,106.5) and (24.5,110.5). Those sites are omitted
by the canary's starting-base-only target recipe. The existing production-goal
controller already excludes owned Refineries and considers broader observed
geysers. Reuse verified target-selection behavior rather than retain this recipe.

The pair's hash-bound conclusion at
`logs/roadmap/resource-reserved-intent-comparison-01/verification.json` is
`closed_interrupted_decoder_comparison`. Affordability fallback starvation is
supported by the saved evidence, but this pair cannot establish reservation
efficacy because a separate physical-target defect interrupts the second arm.
No checkpoint fitting, extra pair, sweep or gate relaxation follows this attempt.
Next verify occupied-geyser exclusion and expansion-site targeting in a native
primitive fixture before another policy comparison. Broad imitation, learned
timing, offensive competence and the full roadmap remain unproven.

## Expansion gas primitive verified before another policy comparison

`refinery_sites(state, catalog)` now selects observed, unclaimed gas near any
completed owned ground town hall, rather than the initial starting base alone.
It excludes occupied gas through `claimed_geysers` and excludes unfinished,
enemy and flying bases. The existing production-goal controller uses the shared
helper, retaining its per-batch claims and worker selection. Broad raw commands
remain available; this is the Terran assistance site's default scope. A regression
using native 09 home/expansion positions fails before implementation and passes
afterward. All 604 default tests pass (40 optional skips); named-file Ruff and
whitespace checks pass.

`logs/roadmap/refinery-expansion-fixture-03/verification.json` independently
verifies a 120-game-second native engineering fixture on AcropolisLE, Zerg
VeryEasy, seed 825101. Debug setup supplies resources, one completed expansion
CommandCenter and four SCVs. All three Refineries are built using normal
commands and native placement queries: two at home, then a free observed site
near the completed expansion. The verifier reconstructs site eligibility,
occupied claims, pending request starts, protected builders and command results
from raw observations, and decodes the replay's three starts and three
completions. Expansion harvesting appears in 451 worker observations and removes
188 gas from that Refinery. Global collected gas increases 580 after its
completion. There are zero immediate/delayed action errors. The cutoff Tie is
normal, with a saved replay. Wall time is 10.197 seconds and sampled host CPU
peak 5.8 percent. This establishes site selection, construction and harvesting
for the fixture, not learned expansion strategy or competitive macro.

Attempts 01 and 02 remain preserved with receipts and source snapshots. They
expose harness defects (tuple positions instead of SDK Point2, then issuing
before debug setup reaches the next observation), and are not counted as passing
primitive tests. Attempt 03 corrects the harness and observes actual payment/
build commands and gas extraction.

The prior decoder pair stays closed as interrupted. Before another policy test,
wire this verified gas-site helper into both newly frozen arms, rather than
reuse the old starting-base-only recipe. Keep model weights and all existing
gates fixed, inspect intent disposition/actual production, and retain separate
scripted, learned-selection and full-imitation claims. No RL is running.

## Corrected gas matched pair: reserved intent passes production gates

The fresh, frozen pair under
`logs/roadmap/resource-reserved-intent-comparison-02/verification.json` is terminal
and independently verified. Native 10 and 11 use the same checkpoint, map,
Zerg VeryEasy Macro opponent, seed 824101, 600-second cutoff and repaired
physical gas-site helper. Separate processes overlap in wall time; reported CPU
peaks include that overlap. Neither arm fits a model or runs RL.

| Replay/native outcome | Cheaper fallback (10) | Reserved intent (11) |
|---|---:|---:|
| New SCVs | 47 | 52 |
| Military births | 0 | 26 |
| Completed production buildings | 0 | 17 |
| Immediate/delayed action errors | 0 | 0 |
| Independently recomputed prediction vectors | 1,195 | 1,051 |
| Frozen engineering gates | Fail | Pass |
| Game result | 600-second cutoff Tie | 600-second cutoff Tie |
| Wall seconds | 58.559 | 65.194 |
| Sampled host CPU peak | 9.3% | 10.8% |

Reserved intent submits 140 of 141 created intents, with zero invalidations and
one explicitly unissued Liberator intent at cutoff. The verifier reconstructs
every budget and selected intent, checks native ability availability, site
eligibility and queue bounds, validates 690 protected pending observations and
53 concurrent choices, and counts actual replay births/completions. Military
births are 18 Marines, five Hellions, one Medivac and two Liberators; MULEs and
enemy ChangelingMarines are excluded. This supports the decoder starvation
repair under this one matched seed. It does not establish learned timing, broad
human imitation, an actual win, or Hard competence. The reserved arm still
requests 20 Factories and 19 Depots: overbuilding remains an explicit limitation.
Original source paths with absolute runner names are also copied into normalized
project-relative snapshot paths, preserving the original hash bindings.

## Longer-game checks expose unit-target builder travel boundaries

`reserved-choice-competence-01` freezes a three-race VeryEasy Macro panel,
AcropolisLE, seeds 824201–824203, 1,200-second game limits and 300-second
per-game wall limits, sequential CPU-only games with the host guard. It stops
after its first Terran game errors; Zerg and Protoss are unattempted. At loop
10912, SCV 4348706817 at (36.4753,143.7095) accepts Refinery targeting geyser
4337696769 at (77.5,145.5). At last logged loop 11360 it is still travelling
with that BuildRefinery order. The point-target route allowance is absent for
unit targets, so the fixed 448-loop timer produces a false timeout. No victory
or all-race competence follows. Its receipt/trace/source snapshot remain saved.

A second panel stops earlier on a 60-second unissued Refinery intent. Its new
route query uses the geyser's blocked centre and returns zero, so it withholds
a build that has a successful placement query. That failed attempt is preserved
as `reserved-choice-competence-02`. Do not extend either deadline to hide these
physical query errors.

`command_point` now shares observed target-point resolution with the request
tracker. `builder_approach_points` retains the actual point for point-target
builds, and offers eight candidates outside a unit target's observed radius
for unit-target construction; native pathing decides which are reachable.
Unobserved unit targets produce no candidates. Regressions are observed red
before the helpers are implemented. All 606 default tests pass (40 optional
skips), with Ruff and diff checks passing.

The native `refinery-expansion-fixture-04` independently verifies the approach
queries: all three geyser centres return zero, while positive approach routes
select the shortest reachable worker and point. All three actual Refinery starts
and completions appear in the replay, and expansion workers extract 188 gas
with zero errors. Debug setup limitations from fixture 03 still apply. Wall time
is 10.470 seconds, CPU peak 23.2% including concurrent default tests.

`run_professional_choice_native_13.py` applies those proven approach queries
to both point and unit targets, preserves the command's actual target, and
derives the existing conservative movement-speed allowance from the shortest
positive route. A third frozen actual-game panel, `reserved-choice-competence-03`,
uses that wrapper, unchanged model and original all-race panel seeds/bounds.
Its active process handle must be inspected before interpreting its outcome.
No fitting, RL, new quotas, attack thresholds or strategic priorities are added.

### Panel 03 terminal: Factory layout feedback is the next boundary

The third panel is now terminal, with only Terran attempted. It stops at the
frozen 60-game-second unissued-intent limit rather than a builder travel timeout.
Its trace-bound `failure-audit.json` identifies Factory intent 328 created at
loop 12604 and still unresolved at last logged loop 13948. All pending requests
have cleared. There are 2,930 minerals and 2,044 gas; affordability is not the
blocker. Native placement/clearance queries find no complete Factory/addon-pad
site at the normal seed or either owned-base fallback. Five Factory-body queries
succeed at some seeds but their addon-pad checks fail, so no complete site is
accepted. This is the current assistance footprint contract, not proof that
every possible Factory location on the entire map is blocked.

Four actual accepted gas requests in this saved trace now have positive approach
route diagnostics and nonzero derived travel allowances. The centre-query
blockage is repaired; observed immediate/delayed action errors remain zero.
The model nevertheless keeps the Factory intent despite placement rejection.
Saved state has 86 workers and 19 military units. There is no callback-completed
game or replay after abort, and Zerg/Protoss remain unattempted. Wall time is
74.235 seconds. Preserve this as a failed actual-game diagnostic, not a passed
all-race panel.

Next address explicit feedback for an intent that cannot be placed under the
current verified footprint/exit rules; distinguish physical-site invalidation
from funding waits and model overbuilding. Do not silently change spacing,
add unit/structure quotas, or resume RL on the basis of the single passed
production canary. The full goal remains active; no simulation handle remains
live from this panel.

### Explicit placement feedback: competence04 (2026-10-07)

The frozen model's native14 execution wrapper releases a physically rejected
intent and excludes its ability for224loops before recheck. Expensive but feasible
choices still retain their savings. No building quotas or score changes were
added. Competence04 records20 placement/path rejections and69 subsequent accepted
commands, then aborts on a Hellion intent at full200supply. Last trace shows116
workers and44military units (84army supply), zeroidleworkers and no pending
requests; observed code14 supply errors affect Liberator, SCV and Hellion requests.
The game remains a failed diagnostic, not a win: no normal callback finish,
replay or attempted Zerg/Protoss games.106.441wall seconds,22.1percent CPU peak,
CPU-only/no training. Saved source hashes and terminal raw trace were audited in
`logs/roadmap/reserved-choice-competence-04/failure-audit.json`.

The placement feedback fix exposes the next defect: resource-ignoring technical
availability must be separated from supply feasibility, and fixed positive-event
choice cadence produces too many workers. Supply masking must account for queued
orders; learned timing and worker allocation remain macro work rather than
permission for hidden strategic quotas.608tests pass with40optional skips.
