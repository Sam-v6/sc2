# Paired-return head geometry results

The stronger parent remains retained. These diagnostics use the same nine
single-action paired outcomes and 3,183 parent states; they establish neither
reliable Hard strength nor generalization. The unused 94000 Medium bank has not
been played by the failed fits.

The zero-step [covariance audit](2026-10-05-paired-head-covariance-audit.md)
passes its stated diagnostic gate. Its fixed ridge is .0002846357463 and matrix
condition is 42,586.78. Independent review verifies all 86 frozen hashes, both
tests, constrained stationarity, full legal-mask preferences and bank metrics.

| Case | Euclidean changed decisions | Covariance changed decisions | Covariance KL |
| --- | ---: | ---: | ---: |
| 92000, wait over SCV | 11.37% | 3.55% | .0001423 |
| 92001, wait over retreat | 6.35% | 1.92% | .0000467 |
| 92003, attack over wait | 6.97% | 3.74% | .0000185 |
| 92007, wait over refinery | 23.69% | 4.71% | .0003870 |

All four independently imposed corrections choose the empirical preferable
full-mask action within the unchanged .005 KL / 5% disagreement limits. They
are algebraic checks, never saved or played policies, and do not prove joint
feasibility. Artifacts: `logs/paired-head-covariance-audit/` and
`logs/audit/paired-head-covariance-independent-review.json`.

The subsequent [whitened joint Adam fit](2026-10-05-whitened-paired-head-improvement.md)
is closed with a failed mechanism gate. It reuses all nine return-order labels,
weights, original objective, Adam settings and bounds; only parameter geometry
changes. Initial inference error is 2.02e-14 with exact legal-mask greedy parity.
The first proposal reduces pair loss .84919 to .75716, but changes 5.435% of
parent-bank decisions, exceeding 5%. Its KL is .0001480. It rejects that proposal,
accepts zero steps, and retains no beneficial preference changes. No evaluation
games, hyperparameter sweep, extension or promotion follows.

Three synthetic tests and independent source/design/artifact review pass. The
review verifies all 95 hashes, reconstructs the rejected proposal without another
actual fit, and checks rollback plus unchanged parent/body/critic/moments.
Artifacts: `logs/whitened-paired-head-improvement/` and
`logs/audit/whitened-paired-head-fit-independent-review.json`.

This failure does not invalidate the individually feasible covariance directions.
The separately declared [joint minimum-change solve](2026-10-05-joint-minimum-change-head.md)
tests all nine preferences together without retuning the closed Adam arms.

The joint minimum-change arm is also closed without gameplay. Its one direct
solve represents all nine empirically preferable full-mask actions, including all
four positive-return alternatives, with pair loss .60354 and anchor KL .0005926.
Its 6.409% bank disagreement exceeds 5%, so its mechanism gate fails. The system
is well conditioned (11.96); kernel residual is 1.86e-16, margin error5.13e-16,
and stationarity residual2.08e-15. It receives no scaling/subset retry or promotion.
The saved head is a failed experimental artifact, not a strength result.
Independent artifact review verifies all 104 hashes, all nine constraints, recovered
multipliers, quadratic optimality, full-mask choices and unchanged parent/body/critic.
Receipt: `logs/audit/joint-minimum-change-head-fit-independent-review.json`.

Following the user-authorized Astra consultation, a separately documented
[amended gameplay protocol](2026-10-05-joint-head-amended-evaluation.md) deliberately
removes the unvalidated disagreement veto after observing this failure. It uses
the same fixed candidate and untouched 12-case Medium bank, with 24 games maximum
and the original gameplay gate. The original failure remains recorded; this is
not a successful original arm or an independently motivated algorithm. Results
are now [closed with failure](2026-10-05-joint-head-amended-results.md):
parent 7/12wins versus candidate 6/12, lower mean return and all three gameplay
gates failed. No extension, refitting against that bank or promotion.
