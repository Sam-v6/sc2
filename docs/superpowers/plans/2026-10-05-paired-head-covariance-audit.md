# Parent-bank covariance correction audit

**Goal:** Check whether the parent hidden-feature geometry admits more selective
single-state directions than the failed Euclidean corrections, before another fit.

**Spec:** [Verified locality audit](2026-10-05-paired-head-locality-audit.md).
This is a new analytical diagnostic, not an extension or retuning of the closed
Adam fit. All parent, paired data and old stability bounds remain fixed.

Augment the 3,183 anchor hidden states with a bias column to form B. Set
C=B.T@B/N and ridge=.001*trace(C)/65, determined solely from the anchor bank.
For each of the same four positive-return pairs q=(h,1), solve
v=(C+ridge*I)^(-1)q. The correction placing +v and -v in the two compared action
columns has factor max(0,.01-old_margin)/(2*q.dot(v)). This minimizes the
ridge-regularized mean squared anchor-logit change subject to that one margin
constraint. No new winner labels, ridge sweep or target-state selection.

Report matrix eigenvalues/condition, each full-mask target choice, bank mean KL,
greedy disagreement and changed-action counts, alongside the prior Euclidean
metrics. Verify the linear solve residual and a synthetic constrained quadratic
identity; hash inputs/source before calculation. Use the existing .005 KL and
5% disagreement thresholds without adjustment.

If at least two distinct positive-return cases meet both bounds, that is support
for separately predeclaring a geometry-aware joint optimizer. It does not authorize
games or prove simultaneous feasibility, generalization or an improved policy.
If not, close the diagnostic and inspect another supported direction. Either way,
do not save corrections as model artifacts or choose them using held-out outcomes.

Limits: zero optimizer steps, games or policy artifact writes. Existing NumPy,
one BLAS thread/CPU under low_load, no downloads/sudo. Artifacts go under ignored
`logs/paired-head-covariance-audit/`; main policy and unused evaluation bank stay
unchanged. Implementation and independent review are the next work.
