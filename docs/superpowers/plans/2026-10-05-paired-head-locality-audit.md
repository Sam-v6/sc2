# Paired-head locality audit

**Goal:** Distinguish the failed bounded Adam direction from a limitation of the
fixed actor representation, using the already frozen paired data and anchor bank.

The reviewed head fit accepts one step, then rejects its second proposal for more
than 5% anchor greedy disagreement. It changes no beneficial intervention choice,
so the arm closes without games. No bound or fit setting is relaxed after results.

For each of the four positive-return pairs, independently calculate the minimum
Euclidean-norm output-head correction that makes the better-versus-parent logit
margin +.01 at that one state. With augmented hidden vector q=(h,1), the margin
gradient has +q in the better-action column and -q in the other column. Its squared
norm is 2*q.dot(q). The unique correction along that gradient is
max(0,.01-old_margin)/(2*q.dot(q)) times the gradient.

Calculate implied logits algebraically, without training, optimizer steps or
writing a policy artifact. Report full-mask intervention argmax, whole-bank
parent||corrected KL, greedy disagreement, and changed-action counts. Report
pairwise normalized augmented-hidden overlaps and teacher margin gaps. Test the
analytical correction against a small explicit synthetic head and verify hashes
before/after all measurements.

This is four independent counterfactuals, not a joint policy or a fit extension.
Passing old bounds for one correction demonstrates feasibility only for that
single inequality; it does not prove simultaneous feasibility, fit convergence,
generalization or improved gameplay. Exceeding bounds is not proof that every
other correction must fail. Do not select a counterfactual as a candidate or run
games. Use results to decide whether the next work should investigate a different
bounded optimization method or representation/locality.

Limits: zero games, optimizer steps and policy artifact writes; CPU/BLAS one thread under
low_load, no downloads/sudo. Freeze input/source hashes before measurement in
ignored `logs/paired-head-locality-audit/`. Main policy remains unchanged.

## Completed audit

The synthetic explicit-head test passes. Independent review confirms all 80
input/source hashes, margins, full-mask choices and bank calculations.

| Seed | Beneficial alternative | Parent margin against alternative | Implied bank KL | Bank greedy disagreement |
| --- | --- | ---: | ---: | ---: |
| 92000 | wait instead of SCV | .545647 | .004511 | 11.37% |
| 92001 | wait instead of retreat | .145288 | .000622 | 6.35% |
| 92003 | attack instead of wait | .066758 | .000091 | 6.97% |
| 92007 | wait instead of refinery | 1.113895 | .015061 | 23.69% |

All four analytical corrections make their target alternative the full-mask
argmax, but every correction exceeds the old 5% disagreement bound; 92007 also
exceeds the KL bound. Changed-action counts are retained, including collateral
SCV/production/attack/retreat changes. The augmented hidden-vector cosine range
is .715916–1.0 across distinct pair rows (some rows share one intervention state).

This supports investigating feature geometry before another plain global head
update. It does not prove that other directions or joint corrections are infeasible.
No counterfactual is saved as a model or selected for games. Receipts:
`logs/paired-head-locality-audit/{inputs,results}.json` and
`logs/audit/paired-head-locality-independent-review.json`.
