# Human-prior sustained-production panel

All six frozen native games and replay/trace checks are terminal and independently
verified in `logs/roadmap/human-prior-native-panel-01/verification.json`. All games
reached the 600-second horizon as ties: zero victories. Opponents were VeryEasy,
not Hard. Same frozen human count checkpoint and pairwise teaching prior, fixed
execution primitives, AcropolisLE, Rush/Macro, seeds 816101–816106; no training/RL.

| Opponent | Depot starts | Living workers | Military births | Action errors |
|---|---|---|---|---|
| Zerg Rush | 54 | 90 | 41 | 0 |
| Zerg Macro | 58 | 87 | 40 | 0 |
| Protoss Rush | 78 | 88 | 24 | 0 |
| Protoss Macro | 57 | 89 | 42 | 4 |
| Terran Rush | 57 | 90 | 40 | 2 |
| Terran Macro | 55 | 85 | 43 | 1 |

All six pass the predeclared opening and sustained-production checks: Barracks
before 90 seconds, four military births, 20 final living workers, a joint
30-worker/eight-army/complete-Barracks observation, and three SCV/five military
births in each middle/late window. These narrow checks prove production continues;
they do not prove competent macro, victories, professional imitation or RL readiness.
Whole-host CPU peaked at 8.7%; native wall time totaled 322.756 seconds.

The most important failure is repeated spending from a standing forecast. All
55 observed Depot order consumptions in Zerg Rush came from one-count proposals;
late order gaps were about 4–13 seconds, although the forecast predicts one start
within 45 seconds. One accepted intent was consumed then another admitted without
remembering its recent fulfilment. Replay confirms 54 starts, not merely submitted
commands. No duplicate ticket execution is needed to produce this overproduction.
The count model's conditional predictions also remain imperfect and its original
labels distinguish building starts from unit births/upgrade completions.

The next bounded cadence diagnostic tracks recent observed order fulfilments
across that horizon, avoids charging current queues and history twice, and retains
original requests through delay. It imposes no unit-specific cap or macro recipe.
This is a rate interpretation experiment with declared start/birth timing and
aggregate queue/history limitations; independently verify its replay outcome and
whether it harms supply, economy or military production before extending it.
Original panel source snapshots are preserved. Do not rerun the unchanged panel
or promote the old count model as a full human imitation policy.
