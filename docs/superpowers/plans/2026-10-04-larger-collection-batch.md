# Eight-game collection batches

Near-greedy collection works better than temperature1 sampling, but its
continuations have not beaten the retained parent across both development banks.
A smaller learning rate reduced policy movement without satisfying the gate.
Each existing update uses only four complete games; the original-rate first
batch contained no victory and changed the distribution much more than later
batches. Five of ten control batches contained no victory. More complete outcomes per update are a distinct hypothesis to test,
not an established cause or promised gain.

Use the existing `--workers 8` option with the original-rate near-greedy source.
It already collects one frozen shared batch before updating. No production code,
reward, observation, action, micro, temperature, optimizer rate, epochs or
minibatch size changes. Preserve the untouched initial bytes and original-rate
four-worker control. The experiment collects eight games per update, doubles
concurrent clients and changes later policy RNG/shuffle boundaries. Opponent
seeds/cases stay matched; only the first four policy seeds/actions are expected
to match the control. Do not claim identical action noise across all40 games.

First run eight parallel 120-second training smoke games on a separate copy,
verify one shared behavior model, successful finite optimizer update and intact
experiment inputs. Then train exactly40 Hard games from the untouched initial,
seed base30000, both maps, all races/five builds, cadence1, 1200 game seconds and
300 wall seconds. Keep at most eight clients; stop on runtime/learner failures.
Record source hashes, actual batches, reward/returns, memory/runtime where available
and finite optimizer payloads. No extra installations are needed.

Freeze the final and evaluate greedy Hard30 on development banks20000 and40000.
Prefer it for further work only if it wins at least14 and13 respectively, the
same rule used for the smaller-rate experiment. If it fails, do not extend this
arm. This is an effort-allocation gate, not statistical proof; the documented
reliable Hard target and reserved final bank50000 remain unchanged.

## Startup verification

The eight-worker training smoke completed eight 120-second horizon ties with
zero failures. All receipts share one behavior model and learner batch; the
finite optimizer payload advanced from 676 to692 updates and144 to152 episodes/
attempts. Experiment initial/canonical remain byte-identical to the untouched
near-greedy initial03633df9bcc83d4c5fab38118e81f1bace82a20030ddaecdf55a943f3777b64a.
Receipt: `logs/audit/near-greedy-batch8-smoke-results.json`.

Independent review verified unchanged source, one shared batch, eight consecutive
policy seeds and finite state. Eight-game collection also changes advantage
normalization, update timing, later RNG/shuffles and concurrency. Four epochs
per sample remain; fewer batches do not mean half the optimizer steps.

Hard40 completed with16 wins/24 losses, zero failures, and wins in each of the
five batches. All22,604 transitions/returns passed audit (maximum return error
3.11e-14). Source hashes and opponent schedules match the four-worker control.
The first four actual gameplay traces are byte-identical across2,573 decisions;
later policies/seeds are not claimed identical. Receipts:
`logs/audit/near-greedy-batch8-first-four-parity.json` and
`logs/audit/near-greedy-batch8-hard-1-results.json`.

The run took236.04 wall seconds for24,189.29 simulated seconds; original-rate
four-worker control took418.31 for26,427.50. Different trajectories prevent a
controlled throughput claim. Helpers took2.69–2.93 seconds, below their120-second
limit. A late once-per-second process monitor observed9.59 GiB peak aggregate
RSS, including shared pages and possibly missing transient peaks. This is not
unique RAM or the absolute peak. Receipt:
`logs/audit/near-greedy-batch8-resource-usage.json`.

Immutable final SHA-256:
2de41e166d2b6f9758123adcab022e085601d35b727231ccdd856fcf1f1c136f.
Its frozen greedy20000/40000 checks completed with10 wins/20 losses and
11 wins/19 losses, zero failures and unchanged hashes. All17,412 and17,181
transitions, discounted returns and greedy choices passed audit (maximum return
error4.27e-14). Both continuation thresholds were missed. Do not promote or
extend this arm. Receipts:
`logs/audit/near-greedy-batch8-final-evaluate-hard30-results.json` and
`logs/audit/near-greedy-batch8-validation-final-greedy-hard30-results.json`.
Production source and retained baseline remain unchanged.
