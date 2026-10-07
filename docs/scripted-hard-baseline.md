# Verified scripted Terran Hard baseline

The initial scripted baseline passed on October 6, 2026: **30 wins in 30 fresh
games**. This proves the declared scripted experiment, not human imitation or RL.
The full learning roadmap remains open.

| Group | Wins / games |
|---|---:|
| Terran | 10 / 10 |
| Zerg | 10 / 10 |
| Protoss | 10 / 10 |
| AcropolisLE | 15 / 15 |
| AbyssalReefLE | 15 / 15 |
| Rush, Timing, Power, Macro, Air | 6 / 6 each |

The contract froze all jobs before results: seeds 819001–819030, step eight,
1,200 game seconds and 300 wall seconds per game, sequential CPU-only operation,
and the 80 percent whole-host guard. Acceptance required at least 21 wins overall
and seven per race. There were no defeats, timeouts or worker failures.
Whole-host CPU peaked at 9.3 percent. Games used 1,459.6 engine wall seconds total.

Each job requested API Hard, protocol value 5. Original replay metadata names
its opponent “A.I.1 (Harder)”; retain both labels rather than silently renaming
the requested difficulty. Higher protocol difficulties are not tested here.

Independent verification checks original replay outcomes and actual tracker
production, reconstructs action-error counts, checks enemy visibility-grid and
weapon compatibility on sampled macro frames, and verifies frozen source plus
engine/map hashes. The runtime asset hashes were captured during the panel;
they are not claimed to be a pre-run asset contract. Visibility trace checks
cover sampled frames, while replay outcomes cover complete games.

The panel recorded 35 raw errors: 26 disabled-actor commands, two close-range
Tank shots, one visibility failure and six ground-target failures around Viking
transformations. Three delayed errors were two siege commands and one construction
reachability failure. Target descriptions in the error audit use the nearest
macro sample and can precede the exact command. These rare failures remain visible
in evidence; victories do not imply perfect execution.

A subsequent guard now suppresses combat commands while Graviton Beam disables
an actor. Its regression failed before implementation and passes afterward.
A native replay query confirms the recorded lifted Marine has no move/attack
abilities while an unlifted control does. The updated full suite passes 455 tests
with 32 optional skips, and the separate native smoke passes. This targeted guard
check is not a new 30-game strength result. The victorious controller's exact
source snapshot remains preserved.

Evidence directory: `logs/roadmap/primitives-hard-baseline-01/panel` contains the
contract, terminal report, independent verification, source snapshot, runtime
receipt, all original replays/traces/catalogues, action-error audit and disabled
Marine query receipt. No replay demonstrations were shown to the user.

Next connect human-selected decisions to the verified worker/construction/combat
execution layer and freeze a new teaching contract on the repaired corpus.
Keep every learned decision and scripted assist attributable in traces. The
production-goal model is an intermediate macro experiment; broader raw-command
imitation, learned attack choices, micro learning/transfer, RL and higher
computer difficulties remain explicit requirements. Do not resume RL before
useful native imitation or relabel these scripted wins as learned wins.
