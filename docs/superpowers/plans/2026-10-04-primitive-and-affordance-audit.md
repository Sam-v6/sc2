# Primitive and affordance audit

The user asked to focus on primitives, sensory information and the RL approach
when continued training fails to improve. The latest independent-value model
fails its joint frozen-development gate despite better value fits. Do not
extend that arm. Keep final acceptance bank50000 reserved.

A frozen-state action audit covers the retained model's60 games/33,556 states
and the independent-value model's60 games/34,158 states. Both use immutable
checkpoints. Legal masks and accepted command flags do not establish successful
completion of every primitive; verify those separately.

| Action | Retained legal games/states | Independent-value legal games/states |
|---|---:|---:|
| Marauder | 5 /31 | 1 /2 |
| Tank | 43 /135 | 53 /170 |
| Starport | 59 /1,768 | 59 /2,017 |
| Medivac/Viking/Raven/BC | 0 /0 | 0 /0 |

Neither frozen model selects these actions. The new model assigns mean
probability1.31e-5 to Starport when legal,2.57e-4 to Tank and1.60e-5 to
Marauder; the retained untempered distribution assigns0.0791/0.1242/0.1106.
These are actual-state probabilities, not alternative gameplay outcomes.
A late-tech action can be technically implemented yet rarely accessible because
resources, producer queues or prerequisites are absent; diagnose those conditions
rather than assuming the model freely chose among all27 actions.
Receipt: `logs/audit/action-affordance-coverage.json`.

Next, verify actual production primitives in an isolated SC2 debug fixture:
producer/tech readiness, resource cost, legal-mask eligibility, command acceptance,
and completed unit counts for the available Terran unit types. Debug resource/unit
creation belongs only to capability verification, never strength evaluation or
training. Instrument prerequisite/resource/idle-producer reasons and observe
normal frozen trajectories around the rare legal opportunities. Separate a real
executor defect from an action-space/credit-assignment limitation.

Only after those findings choose a learning intervention. Possible directions
include sensing/scouting, persistent macro intent, coherent exploration and
training-scale/credit assignment. Do not add a scripted build order or unit mix.
Consult an Astra ideas agent if useful evidence stalls and concrete next steps
run out, as the user explicitly permitted; that condition has not been invoked.

All subsequent local jobs use `tools/low_load.py`, four or fewer simultaneous
games, eight allowed logical CPUs and lower priority. Numerical libraries use
one thread; learning is CPU-only. Eight CPUs bound this task to25% nominal
logical CPU capacity on this32-thread host, with headroom for the user's below40%
whole-machine preference. Other applications contribute independently. Measure
live load during the next runtime job; the first quiet-profile monitor started
after its four games completed, so it is not evidence of active CPU/GPU use.
Child/grandchild resource inheritance is independently tested. The four quiet
verification games finish without failures or checkpoint changes, and known
seed20013 matches its original winning gameplay trace byte for byte. Those
same-race/build runtime checks are not broad strength acceptance.

## Completed capability and live availability checks

`logs/production-capability-fixture/result.json` completes all ten unit types
through the production executor, and builds/attaches all three Tech Labs.
Without labs, Marauder/Tank/Raven/Battlecruiser are unavailable. Queued normal-speed
units make each exercised producer busy and unavailable; accelerated build is
only enabled after that check. Completed unit counts increase for every command.
Debug-created structures, supply and resources bypass normal economy and structure
construction; this does not validate an ordinary build chain or exact costs.
The initial unit batch spends350 minerals/75 gas and the lab batch150/75, but
worker income later changes resources, so no comprehensive cost assertion is made.
No learning transitions or decisions are collected. Fixture wall time9.036 seconds.
Script: `logs/audit/production-capability-fixture.py`.

The read-only availability probe repeats retained frozen games20000 (Terran Rush
Defeat) and20013 (Protoss Air Victory). Both actual decision JSONL files match the
original frozen bank byte for byte; checkpoint0f3e05 remains unchanged. Additional
counters send no game commands. Independent review confirms that design and
fixture limits; primary verification checks both completed traces.

| Condition | Seed20000:523 decisions | Seed20013:406 decisions |
|---|---:|---:|
| Marauder unaffordable |393|278|
| Marauder all ready producers busy |238|183|
| Marauder idle producer without ready lab |165|46|
| Marauder legal |0|6|
| Tank unaffordable |478|369|
| Tank all ready producers busy |187|149|
| Tank legal |3|6|
| Raven no ready producer |523|406|

Conditions overlap. Lab absence is checked only when an idle ready producer
exists, so these are availability explanations, not exhaustive prerequisite counts
or causal explanations of losses. Receipts and replay files:
`logs/production-availability-probe/{20000,20013}.json`;
script `logs/audit/production-availability-probe.py`.

This makes an action-interface limitation worth testing: the policy currently
cannot choose an unaffordable unit to express an intent to save for it; its choice
is masked away until affordable, and cheap production can consume that opportunity.
A persistent macro intent experiment could let RL choose what to save/build next,
while the executor waits for affordability and an idle producer. The agent still
chooses every unit/structure and can cancel/change intent; no scripted build order
or unit mix. This is a hypothesis, not evidence that persistence improves wins.
Before implementation, define bounded intent duration/cancellation, distinguish
selectability from immediate executability, and test ordinary completion/costs plus
unchanged immediate-action behavior. Use a separate archived experiment, preserve
the retained policy and final bank50000, and declare the frozen comparison gate.

The live single-game resource probe now confirms inherited CPUs24–31 and nice+10
in all observed owned processes. Across five two-second windows, whole-host CPU
busy is3.54–5.68%, owned CPU lower bound2.53–4.94%, aggregate RSS peaks1.19GiB
(shared pages double-counted). GPU instantaneous49% at23.70W/40C; separate GPU
process listing shows desktop applications and no SC2/learner. This is evidence
for this single-game fixture, not a peak-load bound for four games or overnight
operation. Receipt: `logs/audit/production-probe-resource-load.json`.
