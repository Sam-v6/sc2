# Joint minimum-change paired-return head fit

Goal: Test whether the empirically preferable paired actions can be represented
jointly with a small change to the frozen parent. The individual covariance
corrections pass the old bounds, while both plain and whitened Adam fits fail
before learning the beneficial choices. Do not retune their step sizes or extend
the closed arms.

Use the same nine paired states, recorded returns and 3,183 anchor bank. Body,
critic and original parent remain fixed. Augment hidden states with bias and use
M=C+.001*trace(C)/65*I, as independently audited. For each pair define its
preferred-minus-other action contrast from the sign of its return difference.
Require an increment d=max(0,.01-current preferred-minus-other margin).
Already-preferred pairs get d=0, preserving their pairwise margin exactly rather
than pushing them further. Include all nine rows, including harmful alternatives.

This is a single equality-constrained quadratic fit: minimize
trace(delta_W.T*M*delta_W) subject to q_i.T*delta_W*a_i=d_i for all nine pairs.
Let K_ij=(q_i.T*M^-1*q_j)*(a_i.T*a_j). Solve K*alpha=d and construct
 delta_W=sum_i alpha_i*(M^-1*q_i)*a_i.T.
Use no optimizer iterations, line search, learning-rate/ridge sweep, checkpoint
selection, or held-out outcomes. If K is numerically rank deficient or the solve
residual exceeds1e-10, close the arm without a policy/game. Verify constrained
stationarity, margin residuals and synthetic minimum-quadratic identity.

This objective uses empirical return ordering, not hand-selected Terran recipes;
it does not use reward magnitude or establish that a single paired trajectory
identifies an optimal action. It is a bounded first experiment in fitting the
observed preferences; generalization must be measured in fresh games.

Save one separately typed frozen head. Before gameplay require the unchanged
.005 anchor KL and .05 greedy disagreement bounds, at least two distinct positive
return cases choosing the preferable action under the full legal mask, exact body
and critic, and independently verified inputs, arithmetic and artifact. Any
failure closes the arm; no smaller subset or scaling retry.

If it passes, use the same explicitly declared, still unplayed 12 Medium cases
94000-94011 (parent/candidate24games maximum) and the unchanged matched gate:
at least two additional wins, nonlower mean return, positive win gain in at least
two races. Frozen race/map/build assignments, 1200 game seconds, 180 wall seconds,
1-second macro, four workers maximum. No Hard acceptance or production promotion.

Separate ignored root logs/joint-minimum-change-head. Freeze source and inputs
before fitting/jobs. CPU-only NumPy under low_load and one BLAS thread; below40%
whole-machine CPU. No sudo/install. Independent design and implementation review
before actual fit; artifact review before conditional gameplay. Preserve all
closed sources/results and the untouched Hard banks.
