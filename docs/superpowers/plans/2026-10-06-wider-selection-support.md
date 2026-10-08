# Separate unit features from context mapping after failed wider fitting

The full-corpus frozen-head fit yields1965/4513exact actors and regresses on774.
Zero exact opposite-label feature collisions does not prove a query can select
each human group, or that one shared context mapping can select all groups.

Use only the already bound117MBteaching cache from `professional-wider-actor-01`.
No replay reconstruction, extra predictions, deployed model update or RL.
Align its4510rows with the saved teaching command identities/exclusions and
verify all selected-group cardinalities. Bind cache/contract/checkpoint/report,
helper and installed SciPy versions before solving.

Give each row its own linear query over frozen entity/geometry/cutoff features,
maximizing a signed membership margin with coefficients bounded[-1,1]. This is
an explicit label-assisted diagnostic oracle. All queries independent, never
used in ordinary inference. Limit each solver to2seconds and total solver phase
to90seconds; CPU one solver thread/two BLAS threads. Save coefficients and
recompute achieved margins directly, verifying finite values and bounds.

Report positive margins, optimal near-zero margins, solver failures and time
limits separately, by singleton/group size and ability. A near-zero result is
not proof of missing raw observations; the frozen encoder may discard useful
information. High independent support with poor actual predictions points to
the shared context/learning path. Widespread independent failure justifies
investigating candidate representation. Neither outcome proves functional
equivalence, generalization or full-game strength. No extension/sweep.

Completed in6.53seconds: all4510solvers are optimal with verified positive
margins;2422singleton and2088group rows, no solver failures/time bounds.
The actual wider model selects1232singletons and732groups exactly among these
representable rows. Stored coefficients are finite/bounded and every achieved
margin is independently recomputed from the hash-bound cache. This supports
investigating the shared context-to-query mapping rather than another candidate
feature change. It does not prove an ordinary context mapping can fit or transfer.
No policy update/native game/RL. Evidence:
`professional-wider-selection-support-01/{contract,report}.json` and coefficients.
