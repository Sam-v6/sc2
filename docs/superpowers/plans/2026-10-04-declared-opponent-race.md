# Declared opponent-race observation

The retained bot first sees enemies at median230 game seconds and enemy structures
at319, usually after contact near home. Across60 frozen games it used Marines and
Hellions exclusively among available combat types. Its live spatial observations
are retained, but early macro observations do not explicitly contain the declared
opponent race. Missing early context is a hypothesis for the shared-policy
limitations, not a demonstrated cause of losses.

Expose three one-hot observations for the opponent's **requested** Terran,
Protoss or Zerg race from GameInfo player metadata. Do not use `BotAI.enemy_race`
or `GameInfo.player_races`, which can prefer actual race. A requested Random
opponent must have all three flags zero even if protocol metadata includes an
actual race. Existing observed-unit information remains available under fog.
No build order, unit mix, scouting timing, reaction or combat behavior is added.

Use an isolated copy of the original-rate near-greedy source. Add only these
three observations, normalized by1. Validate all fixed races and Random with
a conflicting actual-race field, snapshot/encoder output and the full suite.
Migrate the untouched near-greedy initial by feature name: all old parameter and
moment rows exact, new input rows/moments zero, remaining parameters/settings,
RNG/counters and objective exact. Resize only empty rollout-state shape. Reject
old schema in the normal CLI; record migration and raw-logit/value/greedy parity
on retained observations.

Complete separate three-game train/resume/frozen smoke checks across all races.
Then train exactly40 Hard games from the untouched migrated initial, eight
workers, seed base30000, both maps/all races/five builds, cadence1,1200 game
seconds/300 wall seconds. Preserve the preceding eight-worker control and source.
Audit initial gameplay parity after removing only the new observation keys,
then terminal rewards/returns, source differences, finite payloads and settings.

Freeze the final and evaluate greedy30 on each development bank20000 and40000.
Prefer it for further work only with at least14 and13 wins respectively; otherwise
do not extend this arm. Public race identity does not reveal an enemy build or
solve scouting. This is an information experiment, not the final observation
architecture or accepted Hard bot. The reliable Hard target and reserved final
bank50000 remain unchanged.

The isolated archive passed 88 tests and independent review. The three new
tests failed before the source change. The named migration preserves every old
parameter and optimizer row, initializes new rows to zero, and retains all other
state. Initial checkpoint SHA-256:
`3e621df0d99eccb546ad3042a2d1d6a49a897d23a93faec42b4875d85989b98e`.
Across 33,556 retained states, maximum logit/value differences were
4.44e-16/2.22e-16, probabilities differed by at most 9.99e-16, and masked
greedy actions were exact. These are fixed-state checks, not strength evidence.

Actual three-game train, three-game resume and three-game frozen sampling
checks finished without failures; all nine reached the 120-second cutoff.
Declared flags match each requested race throughout, including before enemies
appear. Resume reached 150 episodes/attempts and 692 updates; frozen sampling
left checkpoint bytes unchanged. The canonical initial remains untouched.
The predeclared 40-game Hard continuation is now running. Receipts:
`logs/audit/declared-race-smoke-results.json`,
`logs/audit/declared-race-inference-parity.json`,
`logs/ppo-declared-race/migration.json`.

The first continuation stopped after31 completed games and one SC2 startup
`ServerDisconnectedError` at2.769 wall seconds, before any game decisions.
It is incomplete and excluded from the strength comparison. Preserve its
receipts and updated canonical checkpoint. Repeat the entire40-game schedule
from exact untouched initial bytes in `policy-retry1.npz`, output `hard-retry1`;
no selective replacement or policy/source/settings change. Audit receipt:
`logs/audit/declared-race-infrastructure-failure.json`.
