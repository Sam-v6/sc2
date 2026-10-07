# Source command cohort recovery and causal supervision audit

October 7, 2026. This closes data preparation, not imitation or RL. The scripted
Hard baseline remains separate evidence. No model was fitted or native game run
in this batch. Reliable execution, useful learned decisions, micro transfer and
higher-difficulty wins still require their own evidence.

The previous command-repeat repair covered only game 870. The same conservative
recovery now covers all nine games in the existing six-game teaching / three-game
diagnostic cohort. Each addition requires an original command-manager event,
unchanged known selection context, actual owned actor identity/type, and a unique
unused converted action at the same issue loop. Selection changes remain unknown;
we do not infer commands from eventual units or buildings.

| Cohort | Preserved commands | Added commands | Added production commands | Total commands |
|---|---:|---:|---:|---:|
| Teaching: 294, 870, 955, 839, 991, 523 | 3,898 | 1,201 | 200 | 5,099 |
| Diagnostic: 887, 920, 851 | 1,113 | 536 | 27 | 1,649 |
| Total | 5,011 | 1,737 | 227 | 6,748 |

Teaching games 839 and 523 are human losses; the other seven are wins. Outcomes
remain explicit in the manifest. No winners-only filtering has been applied.
These are reused games, not new diversity or untouched evaluation. Reserved
replays were not accessed. The rebuild recorded 6.3% peak whole-host CPU; this
measurement covers rebuilding, not a separately measured verifier peak.

## What verification established

All old command labels, owned/neutral units, owned memory, player statistics,
map grids/dimensions, effects and upgrades are preserved. History and delays
change to include recovered commands and unknown event slots. Resource-target
normalization is independently checked against the original neutral snapshot and
a unique currently observed resource at the same position and type.

The first preservation check failed because older parents retained enemy data
from before the visibility repair. The final verifier therefore reconstructs
current enemy identities/positions/health and remembered identities/positions
from **every chronological source frame**, including frames with no accepted
commands, without calling PlayerView. It checks the supplied scaled/flipped grid,
source display type and blip state. Source health is compared as float32 to account
for protobuf JSON's decimal representation. All 6,748 resulting states pass.
3,347 old states have changed enemy memory and 1,185 have changed current enemy
observations. Game 870, already repaired, has neither change. These are verified
fog corrections, not preservation of incorrect observations. Coarse source grids
still cannot reconstruct exact native visibility.

Each recovered event checks original manager provenance, inherited selection,
actor membership, exact full converted actor tags, unused wire identity, exact
wire ability, original queue flag and precise original target. The engine may
execute an eligible subset of a selected group; selection membership and exact
converted actors are both checked. Canonical dataset source/code/corpus bindings
and the six/three split validate. Historical parents are unchanged.

## Next-decision labels and the remaining limitation

The next-production target records the next verified human Build, Train,
Research, Orbital or Planetary command and its delay. It preserves same-loop event
ordering and censors any intervening unknown event. A separate backwards scan
independently reconstructs every target; no future target becomes an input.

| Cohort | Production command events | Usable next-decision windows | Windows with positive delay | Censored windows |
|---|---:|---:|---:|---:|
| Teaching | 1,267 | 2,527 | 1,259 | 2,572 |
| Diagnostic | 289 | 645 | 355 | 1,004 |

The usable windows include current production commands and multiple earlier
observations pointing to the same future command. They are not 3,172 independent
human decisions. A same-loop later command can have zero loop delay while
remaining a different event. Unavailable timing is not an instruction to wait,
and a future command label is not an instruction to execute immediately.

The previous future-inventory model caused recurring spending and insufficient
production capacity in native games. Do not repeat that unchanged fit. The next
experiment must learn a current-state decision and timing, use current legal
construction sites and owned producers, preserve non-duplication and resource
budgets, and separately declare scripted mining, supply and micro assistance.
The full raw action space and rich observations remain the final requirement;
a production head is an intermediate experiment. Before broad training, verify
that accepted decisions reach actual mining, foundations and unit births through
the existing primitives, rather than merely logging successful submissions.

## Reproduction and artifacts

Run from the existing worktree with PYTHONPATH=., CPU-only environment and two
OpenBLAS/OMP threads. The completed rebuild is immutable; rerunning it into its
existing output intentionally fails instead of overwriting evidence.

- `logs/roadmap/rebuild_command_cohort_02.py`: completed preparation;
  `human-command-cohort-02/manifest.json` binds sources and code snapshots.
- `logs/roadmap/verify_command_cohort_02.py`: rerunnable independent verifier;
  `human-command-cohort-02/verification.json` records preservation and source checks.
- `logs/roadmap/audit_command_cohort_targets_02.py`: rerunnable target audit;
  `human-command-cohort-02/target-audit.json` binds target files and checks.
- `human-command-cohort-01/failure.json` retains the initial preparation failure
  before any game imported. The second cohort retains the failed preservation
  verifier and final verifier; its initial syntax/tag/translation/float formatting
  assumptions were corrected without changing source data or the importer.

RL remains gated on useful native imitation. This batch supplies neither a
learned victory nor a claim that the complete roadmap is achieved.
