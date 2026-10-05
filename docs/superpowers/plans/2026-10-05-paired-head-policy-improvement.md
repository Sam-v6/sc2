# Paired-reward output-head improvement implementation plan

**Goal:** Test whether the verified single-decision reward discoveries can produce
a stronger frozen policy on separate games, without broad stochastic trajectory
exploration or a scripted macro recipe.

**Spec:** [Completed paired-game pilot](2026-10-05-one-decision-exploration.md).

**Architecture:** Keep the retained observation representation and hidden body
fixed. Fit only its 64-by-27 output matrix and 27 biases from all nine paired
outcomes. Anchor distributions to an unchanged parent-state bank. Store a separate
frozen head artifact, with no PPO or optimizer-resume contract, and evaluate it
through a read-only isolated runtime.

## Fixed fit before implementation

Require complete pilot audit and independent review to pass, with exact input
hashes and unchanged retained parent. All nine pairs enter the fit, including
harmful branches. At each intervention state, prefer the alternative if its
discounted return difference is positive, otherwise prefer the parent action.
Use absolute return difference as its weight, normalized by total absolute
differences; zero differences contribute zero. No human-selected winning action,
worker quota, build sequence, race-specific rule or prescribed attack timing.

Pair objective: weighted binary cross-entropy between the parent and alternative
logits at each recorded intervention state. Anchor objective: 10 times mean
KL(parent distribution || candidate distribution), with the recorded legal masks,
on all 3,183 states from the six original probe games. Cache hidden activations
using the fixed parent body and project encoder. Preserve all body and critic
parameters; do not fit a critic, recollect trajectories or use PPO buffers.

One deterministic full-batch Adam fit, fresh zero moments, learning rate .003,
betas .9/.999, epsilon 1e-8, maximum 256 steps. Begin from the parent head. Check
each proposed step against mean anchor KL <= .005 and greedy disagreement <= 5%
on the whole fixed bank. Stop at the first violation and retain the preceding
feasible head; rejected proposals count toward the 256-step budget. Do not search
learning rates, objective weights or change bounds.
Report pair loss, anchor KL, disagreement, accepted steps, gradient norms and
intervention preferences. This is one bounded improvement attempt, not a sweep.

Before games, require at least two distinct positive-return case seeds to choose
their empirically better alternative greedily over the full original legal mask,
with both anchor
bounds met and all non-head arrays byte-identical. Otherwise close without game
evaluation. This is an implementation/mechanism gate, not a strength result.

The artifact contains only fitted head arrays and explicit parent/source/schema
provenance. Default PPO checkpoint loaders must reject it; the isolated frozen
evaluation loader checks its parent hash, schema and finite shapes. No optimizer
state is promoted or silently attached to old global PPO clocks.

## Separate matched Medium gameplay gate

If fit and independent review pass, evaluate unchanged parent and frozen candidate
on exactly 12 cases, seeds 94000–94011. Race cycles Terran/Protoss/Zerg by seed
offset; map alternates Simple64/TritonLE; builds cycle Rush/Timing/Power/Macro/Air
by offset. Freeze explicit cases and verify the seed bank is unused before fitting.
Both arms use one-second cadence, 1,200-game-second limit and 180-wall-second
limit, with no updates. Maximum 24 games, no outcome-driven repeats.

Candidate must win at least two more cases than parent, have no lower mean
discounted return, and have a positive matched win difference in at least two
races. Full recorded-choice/reward/immutable-artifact audit and independent review
must pass. Failure closes the arm without extension or promotion. Passing permits
a separately declared larger comparison, not final Hard acceptance. Reserved
Hard final cases remain unused.

## Implementation and review checks

- [ ] Freeze source/input manifests; prepare paired states, parent hidden bank,
  masks and reward weights using the current project encoder.
- [ ] Test head-loss gradients against finite differences, zero-weight handling,
  anchor-bound rollback, immutable body/critic arrays, and frozen-only artifact
  schema/hash rejection.
- [ ] Run the one bounded fit on CPU; independently review numerical results and
  mechanism gate before any games.
- [ ] Run and audit the declared matched games only if eligible, retaining all
  failures and respecting interruption receipt retention and complete coverage.

Limits: existing NumPy/Python, CPU only, one BLAS thread under low_load, at most
four total SC2 engines, total CPU preference below 40%, no sudo/downloads. Work in
ignored `logs/paired-head-policy-improvement/`; main policy/CLI stays unchanged.

## Design preflight

Independent design review finds no material blocker. Its implementation checks
are incorporated above: distinct case seeds, full legal-mask preferences, rejected
proposal budget accounting, and fresh evaluation cases frozen before fitting.
`logs/audit/paired-head-design-review.json` records the review. The 94000–94011
bank was not found in prior scanned audit/input manifests; search scope is recorded
in `logs/paired-head-policy-improvement/seed-bank-check.json`.
Fitting, frozen artifact implementation and evaluation have not run yet.
