# Fixed-batch diagnosis of the failed production-input learner

The matched production-input experiment is closed: parent22/30, control21/30, sensory6/30 Medium wins. Independent complete audits pass. Before changing temporal credit, test whether fresh-input Adam age and critic gradients cause excess first-update actor movement. This is an offline mechanism diagnostic, not another game-training arm or a playing-strength test.

## Fixed inputs and fidelity gate

Use only original first training cases88144–88147. Their3898decision traces match byte for byte across control/sensory, including sampled actions, masks, rewards and durations. Preserve original parent0f3, sensory initial3232, first promoted control ea531 and sensory af080 files/hashes, reward/gamma/cadence/settings and all old parameters/moments/counters. Cached new features come from those recorded snapshots. Reconstruct states, legal masks, chosen actions, old log probabilities, finite lambda1 advantages and returns. Last next-state content is immaterial only because its terminal continuation is zero; do not infer other unrecorded engine state.

Restore the original parent RNG and reproduce all four policy-seed draws before the four epoch permutations. Freeze complete minibatch orders and input/source hashes before replay. First require factual sensory A and old-input control E to reproduce all archived first-update network and Adam arrays within absolute1e-10/relative1e-10, exact updates740 and RNG state. Stop and repair any fidelity failure before interpreting interventions. Never consume smoke-updated weights.

## Five fixed replays

| Arm | Appended-row Adam age | Critic gradient into appended rows |
| --- | --- | --- |
| A factual sensory | Original inherited676 | Enabled |
| B age only | Fresh0 | Enabled |
| C gradient only | Inherited676 | Blocked |
| D both | Fresh0 | Blocked |
| E old-input control | Original676 throughout | No appended rows |

In B/D give only appended rows a separate Adam clock. Preserve all old parameter ages/moments and every other setting. In C/D block only the value-loss gradient into appended first-layer rows; actor and entropy gradients there and critic gradients elsewhere remain. Forward algebra and initial outputs stay equivalent. Hold clip/entropy/value coefficients, minibatch order, advantages, returns and global max-gradient rule0.5 fixed; actual clipping factors may differ with intervention and must be reported. No learning-rate, temperature, reward, cadence, head, primitive or exposure changes.

At every minibatch report appended actor/weighted-critic/entropy gradient norms, actor–critic cosine, global clipping factor, actual row movement, and hidden-preactivation movement. Compare original-parent to updated masked categorical policy KL, greedy disagreement and wait probability on all3898fixed training states and the separate3183instrumented probe states. Report value error on the fixed training targets separately; probe trajectories are greedy/off-policy, so do not label their outcomes as held-out categorical-critic validation. Freeze probe/source/input hashes before measurement.

## Interpretation and stopping

Primary descriptive materiality check at the final update: on the separate probe states, factual excessKL=KL_A−KL_E must exceed1e-8. An intervention materially reduces this excess if KL_intervention−KL_E is at most half the factual excess. Report absolute KL, disagreement, wait shift and all intermediate metrics, including negative excess; do not hide near-tied argmax sensitivity. Apply the same check to B/C/D without selecting new thresholds. Results distinguish age, critic pathway, interaction, or lack of a first-update explanation. They cannot establish stronger play or explain later trajectory shifts by themselves.

No more than5×64optimizer minibatches, no SC2 games or gradient-bearing state selection. CPU-only existing siblingTorch via absolute non-resolved interpreter, Python-B, low_load eightCPUs/nice10/BLAS1 and Torch1thread; per-arm offline wall budget600seconds. Sources and artifacts stay in owned worktree; preserve all failed-arm evidence. Independent review must reconstruct fidelity and metrics before any next game experiment is separately declared. Do not integrate intervention checkpoints or promote the failed sensory model.

Status: predeclared only; no optimizer replay has run.
