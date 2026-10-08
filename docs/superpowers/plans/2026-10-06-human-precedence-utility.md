# Sparse family utilities for human production precedence

Both tree fits are terminal without checkpoints. The16thread retry stopped at
602.77seconds after its optimizer marker, reason `optimizer_wall`, peak87.9percent
whole-host CPU. The CPU guard did not see three consecutive over80samples.
Preserve both failures and do not extend the tree budget. This experiment changes
representation to avoid repeated full-state rows for every family comparison.

Use the exact independently verified49,662teaching and19,179development base
pairs, IDs, labels, event/game weights and splits from `human-production-precedence-01`.
Normalize teaching weights to sum1. Original plus mirrored loss/gradient is
mathematically equivalent to original pairs alone with normalized weights; verify
that equivalence in tests. No future commands or sampling information become
model inputs. The frozen count model remains the proposal source.

For each current masked state x, learn52family utilities s_f=x*w_f+b_f. The
probability that f precedes g is sigmoid(s_f-s_g). Compute one sparse state
matrix's utilities, gather pair differences, and scatter residual gradients.
Do not expand states across pairs or densify the sparse observation matrix.
Use teaching-only nonzero columns and RMS scaling with declared0.01floor. One
untuned L2 coefficient0.01 on weights, zero initialization, centered saved biases.
Unsupported teaching families remain explicitly unsupported for future live use.

One L-BFGS fit: maximum200iterations, maxcor10, gradient1e-5, relative loss1e-9,
600optimizer seconds and900total seconds, two CPU threads, GPU disabled. Estimate
parameter/history memory before fit. Save only finite parameters and status;
timeout or iteration-bound status is explicitly nonconverged. Do not promote a
solver failure. Keep the existing frozen offline accuracy, macro-family, building
and support gates unchanged. Reconstruct labels and reload probabilities and
metrics before use. Also report worker/building pairs and per-game accuracy.
No seed/regularization/budget sweep.

Fresh outputs `human-production-utility-01/`, guarded optimizer-start marker.
If the fit passes verified gates, implement the existing tested intent/persistence
and reservation contract, then its frozen same-job native comparison. Linear
family utilities can miss nonlinear human priorities; a failed gate closes this
variant rather than triggering more iterations or scripted macro priorities.
The full broad-command roadmap and micro/RL/Hard goals remain unfinished.
