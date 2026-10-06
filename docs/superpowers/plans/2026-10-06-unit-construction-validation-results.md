# Exact unit construction validation: verified result

The resolver now validates unit-target construction at exactly the selected visible
unit's position. A successful check returns the original command unchanged; an
invalid or unobserved target produces no dispatch and no substitute target.
Existing point resolution is unchanged. Native packet/decision/history recording
covers both paths. No build strategy or reward updates are introduced.

RED tests show missing queries and invalid construction passing through; GREEN
checks verify one exact target-position query, original command/group/queue/mode,
rejection and no hidden-target query. Normal392tests (31optional skips), focused
32Torch/execution checks, Ruff/diff and independent review pass.

## Frozen native result

Watcher72828 and verifier12437 are terminal exit0. Same frozen model, profile,
candidates, placement option, fixed ability/game seeds and180second opener as
before.101decisions/98dispatches;94Success/4NotSupported. Two refinery intentions
are blocked by exact-position placement responses44(CantBuildLocationInvalid);
one CommandCenter intention has no legal local position. No blocked intention
enters dispatched history. Three point adjustments remain.

Final player stats:24workers,840minerals,268gas,25/46supply, noarmy. Twelve new
worker tags are observed across the trace; final visible workers23exclude an own
worker not currently in the visible-unit list. Final structures include two
CommandCenters (one initial), twoDepots and oneRefinery; noBarracks. The remaining
fourNotSupported submissions are Smart commands, not refinery construction.
Whole-host CPUpeak6.3%; noGPU, fitting, resource stop orRL.

The prechange trace independently shows all three refinery errors selecting a
geyser exactly overlapped by a visible ownRefinery: two complete, one under
construction. The new engine response confirms invalid selected placement in the
new trajectory. It does not prove every oldNotSupported code had the same cause.
The changed history/trajectory means opening counts are not a controlled strength
comparison. No checkpoint/seed selection, extension or promotion.

Independent reconstruction reproduces every sampled command and both exact-unit
and local-point requests/responses/helper decisions, actual dispatch/history,
rejection/adjustment counts and action results. Evidence:
`logs/roadmap/unit-placement-human-native-01/verification.json` plus its bound
trace/static/episode/replay/telemetry/checkpoint files.

## The next problem is learned production intent

A read-only diagnostic identifies41of101logged states in which the engine lists
Barracksconstruction for eligible workers. The model gives it only.37%,.25%,.30%
probability at the first, middle and last such state (loops1806,3170,3987), while
Smart/Attack/TrainSCVdominate. So absence ofBarracksis not explained by command
availability alone. This fixed three-state inspection does not establish all
causes or justify a probability floor/build recipe. Evidence:
`logs/roadmap/unit-placement-human-native-01/barracks-score-diagnostic.json`.

The six fitted human games contain18Barracks commands and355TrainSCV commands;
they cover approximately8to14minutes each and include162Marine training commands.
Army demonstrations are present, but the current next-command policy rarely
selects the production step. No more unchanged fits or small execution-only
opening tweaks are justified by this finding.

Next investigate human macro intent separately from frequent movement commands:
for each causal replay state, derive the next retained human production/build/
research decision and the time until it, as supervised targets only. Preserve the
full existing raw controller and actor/target grammar; no future labels may enter
inputs. First audit label coverage and game-disjoint predictability before wiring
an additional scheduled decision stream or starting another full-controller fit.
This is a human-imitation experiment, not RL and not a prescribed build order.
Useful full-game imitation, learned micro transfer, reliable all-raceHard and
higher-difficulty evaluation remain open.
