# Covariance-whitened joint paired-return head fit

Goal: Test one joint policy improvement after the zero-step covariance audit
showed all four independent positive-return corrections within the original
stability bounds. Require independent verification of that audit before fitting.
Single-state feasibility does not establish joint feasibility or generalization.

Use exactly the frozen nine paired states (including harmful branches), absolute
return-difference weights, and 3,183 parent anchor states from the closed original
head fit. Keep its weighted binary cross-entropy + 10 mean parent-to-candidate KL
objective, .005 KL and .05 greedy disagreement limits, fixed body and critic,
fresh Adam (.003, .9, .999, 1e-8), and maximum 256 proposals. Stop at the first
infeasible proposal, retaining the preceding feasible head. No sweep or retry.

Only change the parameter geometry. Augment hidden features with a bias column;
use the independently audited C=B.T@B/N and ridge=.001*trace(C)/65. Compute the
symmetric positive definite square root S and inverse square root T of C+ridge I.
Whiten features as B*T and parameterize the augmented head as theta=S*W. Thus
B*T*theta=B*W initially. Fit theta with the same objective and Adam settings,
then convert back W=T*theta. The anchor bank alone determines the geometry;
paired labels and future evaluation outcomes do not select eigenvalues or ridge.
The small numerical reparameterization error must be measured before fitting.

Before any gameplay, require at least two distinct positive-return cases whose
full legal-mask greedy action becomes the empirically better action, both original
bank bounds, and unchanged body/critic/parent/source. Evaluate only the final
retained feasible proposal; do not select a previous checkpoint by pair labels.
Require independent implementation and artifact review. Failure closes the arm.

If the mechanism gate passes, evaluate exactly the already frozen, still unplayed
12 Medium cases 94000-94011, each parent and candidate (24 games maximum), using
original race/map/build assignments, 1200 game seconds, 180 wall seconds, 1-second
macro and four workers maximum. Source/input hashes frozen before jobs. Same
matched gate: candidate gains at least two wins, nonlower mean return, positive
win gains in at least two races. No extension on failure. This is discovery-stage
Medium validation; no Hard acceptance or production promotion. Hard development
and reserved acceptance banks remain unplayed by this arm.

Use a separate ignored root logs/whitened-paired-head-improvement. Preserve the
closed plain-head fit and diagnostic sources/artifacts. NumPy, BLAS one thread,
CPU-only low_load; below 40% whole-machine CPU; no sudo/install. Tests cover exact
initial logits, transformed gradient finite differences, and rejected-proposal
rollback. All nine pairs and empirical return magnitudes remain visible.
