# Sampled human policy: verified opening result

Explicit `--ability-seed` samples the frozen GoalFirst ability distribution after
engine candidate masking, at temperature 1. Arguments remain greedily selected.
The default decoder, forced labels, supervised objective and checkpoint weights
are unchanged. A local NumPy RNG is initialized per native agent; receipts store
its seed. Empty candidates and scheduled waits consume no draws.

New interface tests failed before implementation and then passed. Tests compare
seeded draws against an independent two-class probability calculation and check
reproducibility, caster masks, unchanged inputs/weights/default choices, and
non-consumption of randomness for forced choices or empty candidates. Normal
suite: 387 tests, 31 optional skips. Focused CPU-Torch suite: 23 tests. Independent
implementation and supervisor/verifier reviews find no blockers. Ruff/diff pass.

## Actual native behavior

Watcher 59273 and verifier 15655 are terminal exit0. Fixed ability seed120603,
game seed120602, frozen baseline checkpoint, prior professional input profile and
engine candidates; AcropolisLE/VeryEasyZerg/RandomBuild; 180 game seconds, cap32.
This is a deliberately truncated opener, not a completed game or a victory.

| Observation | Result |
| --- | ---: |
| New observed worker tags | 8 |
| Final workers | 20 |
| Completed supply depots | 1 |
| Completed refineries | 1 |
| Barracks | 0 |
| Final minerals / gas | 1365 / 268 |
| Final supply used / cap | 21 / 23 |
| Decisions / dispatched commands | 112 / 112 |
| Successful submissions | 103 |
| Placement failures | 4 |
| NotSupported submissions | 5 |
| Unavailable blocks | 0 |
| Peak whole-host CPU | 6.0% |

Final native observations explicitly show build_progress1.0for the depot and
refinery. The refinery first appears in a logged observation at26.07seconds;
the depot at81.25seconds. This depot timing is late; no useful army appears.
Choices comprise69Smart,20Attack,12TrainSCV,6BuildRefinery,3BuildCommandCenter,
1BuildSupplyDepotand1BuildBarracks. No build order or reward updated the policy.

Independent reconstruction reproduces every masked categorical draw, decoded
argument, delay, raw query response interpretation and dispatched history from
the recorded seed/profile. Checkpoint/source/profile hashes and prior comparison
chain validate. CPU-only, no resource stop, no fitting or RL. Evidence:
`logs/roadmap/sampled-human-native-01/verification.json`, bound raw traces,
static/episode/replay/telemetry files, fixed checkpoint and source profile.

## What this establishes and what comes next

The single-highest-score decoder previously produced only three new workers and
no buildings. Sampling those learned scores yields actual economic construction
in this one opening. This shows why deterministic command matching alone can
understate behavior available in the learned distribution. It does not repair
the failed held-game imitation gates, establish competent planning, or select a
checkpoint/seed for acceptance. Do not extend or sweep the closed diagnostic.

The engine rejects three CommandCenterpositions and one Barracksposition with
CantFindPlacementLocation. Repeated refinery and Smart submissions account for
NotSupported responses. Targets and placements remain a separate execution
problem even after ability/caster filtering.

The repository already has `src/learning/placement.py:resolve_placements`, tested
for nearest legal local positions, preserving learned ability/group/queue, and
rejecting construction when no legal candidate exists. The next justified change
is explicit opt-in integration of that existing primitive into this native adapter,
with requested versus dispatched commands kept distinct and engine placement
queries recorded for reconstruction. It must not invent a build choice or build
order. No new full-controller fitting or RL is justified by this opening alone.
Useful full-game imitation, learned micro transfer, reliable all-race Hard wins
and higher-difficulty evaluation remain open.
