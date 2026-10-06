# Human intention probe: completed, inconclusive

The teaching-only diagnostic completed in 42.702 seconds using existing NumPy/SciPy, two CPU threads and no GPU. Whole-host CPU peaked at 7.2% across 9 watchdog samples; no resource stop occurred. All 4,513 retained command rows were used as ability labels, including three rows lacking complete-command actor/target labels. No774or reserved replay inputs or predictions were used.

All nine fixed L-BFGS-B fits reached100iterations without convergence. Their scores are descriptive and inconclusive; no arm passes the declared signal criterion. Do not extend this closed diagnostic or claim current state is insufficient based on it.

| Held games | State exact macro recall | History | Both | State macro false positives |
|---|---:|---:|---:|---:|
| 294/887/920 | 1.81% | 9.64% | 9.04% | 3.85% |
| 870/839/851 | 2.17% | 11.76% | 10.53% | 10.64% |
| 955/991/523 | 1.75% | 10.50% | 10.28% | 9.05% |

The frequency baseline predicts Smart and has zero exact macro recall in every fold. Held labels absent from teaching occur in folds2and3and are explicitly counted as errors; the first fold has no absent ability labels.

Independent reconstruction reproduced all4,513source feature rows, every saved prediction and per-game/aggregate metric, all training-only RMS scales/nonzero columns/classes, and the failed signal gates. The fixed first three failed state-arm macro rows per held game yield27source audits:18TrainSCVand9BuildSupplyDepot, all predicted Smart. These are common teaching abilities. Recorded resources, worker counts and supply cap are available; food_used, idle_worker_count and army_count are unknown in all27. This shows failures in basic opening decisions, but does not establish missing supply as the cause. The source audit cannot prove native action legality or hidden prerequisites.

The next useful check is optimization and source ambiguity, not another full-controller sweep: examine saved-model training loss/gradient and whether basic opening decisions have distinguishable causal inputs. Nonconvergence must be resolved before interpreting this linear diagnostic as evidence for or against a representation. Missing fields and command redundancy remain hypotheses requiring source evidence. Do not introduce invented native fields or human UI selection.

RL stays stopped while useful human imitation and native controller competence are unproved. Learned micro transfer, reliable all-race Hard evaluation and higher difficulties remain open.

## Frozen artifacts

- `logs/roadmap/intention-probe-01/contract.json`: `9f72f3253a3c0de339888267eaf4da15bcda23782528d5aa22bbcdb62676651b`
- `logs/roadmap/intention-probe-01/report.json`: `6f25a04e5498fb310dcc0794234115227443fe2a02c9f42903526b9b62ef4c6b`
- `logs/roadmap/intention-probe-01/verification.json`: `b19d467a5c2228e97ace5181b14ac81226647e02803bffe5b0689ac6b572d7f9`

Run/watch/verifier wrappers are retained underlogs/roadmapwith SHA bindings. Implementation/runner/independent-verifier reviews found no remaining blockers after explicit terminal-timeout handling; no model was promoted.
