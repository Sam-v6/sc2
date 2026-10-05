# Macro teacher feasibility: complete, all-race gate failed

The literature's competent-imitation initialization is now tested through the
existing learner interface. A training-only selector chose the same27legal
macro actions, using causal current scalar observations and unchanged execution,
worker/micro behavior, reward, resources and cadence. No learned policy was fit;
the retained checkpoint supplied reward/schema context only, never action weights.

The frozen12Hard cases125000–125011 completed with no infrastructure failures
and8,721decisions. Native session38701 terminated with exit0. Every replay remains
unopened. Reserved final acceptance cases50000–50029 remain unused.

| Opponent | Victories | Defeats | Time-limit ties |
| --- | ---: | ---: | ---: |
| Terran | 1 | 2 | 1 |
| Protoss | 4 | 0 | 0 |
| Zerg | 3 | 1 | 0 |
| Total | 8 | 3 | 1 |

The declared gate required8total victories **and at least2against every race**.
Terran support fails, so this teacher is not used for cloning, extended or tuned
on this bank. These scripted victories establish neither learned strength nor
reliable Hard acceptance. Failure alone does not establish interface inadequacy.

Independent review verifies frozen inputs/source/context, exact legal requests,
ordinary rewards, journals, typed demonstrations, native replay headers and
observer records. Demonstration metadata explicitly prohibits on-policy PPO
reuse. Queued commands are not engine acknowledgements; appearances/completions
include initial units/buildings. All optimizer/update counts remain0.

CPU monitoring recorded133two-second whole-machine windows: mean12.5452%,
maximum23.2558%, below the80%ceiling. Frozen controller/configuration and batch
coverage enforce at most4workers; no continuous independent process census was
recorded. No GPU task ran.

Evidence: `logs/macro-teacher/preflight/{inputs,ledger,summary,cpu-windows}.json`,
individual raw action/journal/production/command/trajectory/replay records, and
`logs/audit/macro-teacher-complete-independent-review.json`.
Prepared inputs SHA256:
`bef330abdf6897ae7d1aa31fde82280e23162b0dd358a2102b37b1319be6b56f`.

Read-only diagnosis (`tools/macro_teacher/diagnose.py`, output
`logs/macro-teacher/preflight-diagnosis.json`) shows actual appearances of tanks
and medivacs in the failed Terran cases, substantial army losses after the first
attack, and heavy replacement Marauder requests. Thus absent advanced-unit
production is not a sufficient explanation. The summaries describe observations;
they do not distinguish poor composition/attack timing from combat micro defects.
The next investigation must resolve that distinction before another bootstrap.
