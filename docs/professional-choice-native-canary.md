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
