# Repaired professional source imitation: closed, not promoted

The paired source-version trial completed and independently verified. Both arms
finished30epochs,6,390optimizer updates and101,940example presentations. Original
optimizer time339.20seconds; repaired346.31seconds. Whole run879.43seconds,
peak whole-hostCPU11.6%; verifier peak8.2%. No guard stops, GPU, native games,
RL, reserved replay evaluation or checkpoint promotion occurred.

All9,318ordinary predictions and2,226own-history predictions independently
reproduce, alongside input/source hashes, initial weights, teaching support,
sampling schedule, actual exposure, metrics and gates. Verification receipt:
`logs/roadmap/repaired-production-imitation-01/verification.json`.
Comparison SHA256:
`dbac15fc99e22570695bae4b626156e61b247b41b7e2cc8a8641b754fa4923c0`.
Contract SHA256:
`4e85ce4716ab286005e2bdcc608cc22ee582551b628cc976b49deb5169211cda`.

| Same evaluation | Original-source fit | Repaired-source fit |
| --- | ---: | ---: |
| Held exact macro ability | 27/262 | 21/262 |
| Held complete commands | 31/1,113 | 28/1,113 |
| Held macro false positives | 30/851 | 33/851 |
| Held macro with own-prediction history | 10/262 | 4/262 |
| Recovered teaching ability choices | 0/146 | 26/146 |
| Recovered teaching complete commands | 0/146 | 19/146 |

Matched budgets and false-positive tolerance pass; all five improvement gates fail.
The trial is closed without extension, seed/weight sweep or native test. Source
repair also changes derived history/timing on shared rows, so results measure the
whole source-version intervention, not just additional command labels. Held games
have earlier development use; these are not fresh acceptance results.

There is a useful conditional-copying result on the146new teaching commands:
given the correct ability as a named diagnostic oracle, the repaired model copies
122complete commands, versus3for the control. Given ability and actors, it copies
146/146. Ordinary ability choices remain26/146:24Hellions,1Thor and1Orbital;
zeroSiegeTank/WidowMine/Planetary choices. It learns much of execution for these
commands but usually chooses another action. This is teaching-state conditional
reconstruction, not autonomous competence or a diagnosis of all controller errors.

The next human-only investigation should test whether upcoming production intent
and timing can be learned separately from the human's next click. A raw next-command
model is dominated by frequent movement/selection-of-target commands. That is a
plausible explanation to test, not a proven sole cause. Use target-only future
production labels with existing unknown-event censoring; keep future state/actors/
targets out of inputs. Audit signal and development generalization before a new
full-controller experiment. Preserve the broad raw controller and all observations;
a production diagnostic is not the final action-space restriction.

Data recovery remains valid even though this fit failed. Useful human imitation,
native sustained army production, learned micro transfer, all-race Hard wins and
higher-difficulty evaluation remain unachieved. RL stays off during the human
imitation phase.
