# Human production ordering experiment

The scripted baseline remains 30/30. Human production imitation has not yet
produced a useful native controller. RL stays paused; the full roadmap is open.

## Runtime and representation

The independently verified ordering dataset contains 49,662 teaching and 19,179
development base pairs. Each compares the next original human command for two
production families. Repeated source-event pairs receive controlled weights;
future commands are targets only. Proposal-only evaluation uses candidates from
the frozen count model, avoiding future-informed candidate admission.

The first two-thread ExtraTrees fit was manually stopped after exceeding the
intended optimizer duration. Its original watcher enforced only a total deadline;
the optimizer assertion happened after return. The sixteen-thread retry used the
exact same pair files and learning configuration, but a corrected hard optimizer
deadline. It stopped at approximately 602.77 seconds, with no checkpoint, reason
`optimizer_wall`. CPU peaked at 87.9 percent briefly; the guard did not observe
three consecutive samples above 80 percent. Neither tree run produced a quality
result. Do not retry them unchanged or increase their training budget.

The sparse utility experiment computes one score per family and observation,
then compares scores. It retains the same supervision, proposals and acceptance
gates. Teaching-only active columns and RMS scales are used; no sparse states
are expanded across pairs. Four meaningful tests verify expanded-data equivalence,
finite-difference gradients, common-bias invariance and mirrored-pair equivalence.
The parameter array is about 0.38 MB, estimated L-BFGS history 8.36 MB, and score
matrix 2.24 MB. Source observation matrices remain sparse.

## Utility quality result

`logs/roadmap/human-production-utility-01/model.pkl` was written approximately
6.23 seconds after its optimizer marker. That includes checkpoint writing and
is not a precisely recorded fit duration. Its status is `iteration_bound`;
optimization did not converge. Exact iteration/objective-call counts were not
persisted before an evaluator variable collision. The saved finite checkpoint
was evaluated with a corrected script; no refit occurred. Fit-run CPU peaked at
9.8 percent; the corrected evaluation peaked at 6.8 percent.

| Development pairs | Utility accuracy | Teaching-derived pair majority |
|---|---:|---:|
| All 19,179 | 75.21% | 75.92% |
| Proposed 11,522 | 79.25% | 80.24% |
| Proposed with a building, 7,714 | 80.27% | 82.24% |

Proposal-only macro-family accuracy is 87.2104 percent versus 87.2543 percent for
the majority baseline. Support and building minimum gates pass; accuracy and
macro-family improvement gates fail. The utility model therefore is not promoted
to native play. A fast fit and plausible accuracy do not prove useful game behavior.

The majority baseline is a table fitted from human commands, not a hand-written
build order. It is nevertheless unconditioned on current observations and cannot
be called a complete professional imitation controller. Any native use must be
a separately declared diagnostic of request execution, with counts/checkpoints,
assistance and attribution frozen. The failed utility model's gates remain failed.

Independent verification reconstructs original command pair labels and weights,
reloads predictions, and recalculates primary and grouped metrics/gates. Preserve
all `logs/roadmap` receipts and snapshots. See the execution ledger for terminal
verification status and the next controlled intervention.
