# Combined combat and collection results

The [declared experiment](2026-10-05-combined-combat-collection.md) completed all
64 Medium training games and passed independent full-data review. Results were
1 victory, 55 defeats and 8 horizon ties. This verifies the training loop and
intermediate feedback. The separate ordinary-scoring Hard comparison failed:
parent 4/12 wins, candidate 0/12, with lower mean discounted combat return. This
arm is closed without promotion, extension or final acceptance.

## Objective and training

The separate `combat-kills-collection-v1` checkpoint context retained the
original per-transition enemy unit/building destruction value, terminal victory
bonus and discounted potential shaping. It added authoritative mineral/gas
collection increments worth one tenth of enemy destroyed value in the same
resource units. Spending, refunds and loss counters do not earn harvest credit.
It retained the 5,460-feature live/fog observation representation, 27 atomic
macro choices, original discount and PPO settings. Worker/combat execution stayed
scripted; macro choices remained learned. No build order, army mix or worker
quota was added.

Initialization preserved the retained parent's actor and RNG exactly, while
resetting the critic, all Adam moments/age and task episode counters together.
The final checkpoint was chosen before games as the only evaluation candidate;
no earlier model was selected after observing results. All 64 fixed cases
114000–114063 completed in 16 four-game batches, with 54,215 decisions and
868 actual optimizer minibatches. There were no replacements or extensions.

The independent full audit reconstructed all stochastic choices, reward terms,
Monte Carlo returns, advantages, likelihoods, journal events and replay headers.
It reconstructed canonical seed draws, behavior snapshots, merged learner inputs
and optimizer/RNG/counter chains. All 16 native helper replays, run only on
disposable /tmp copies, matched every numeric network/moment array and metadata
exactly. Its immutable receipt binds 486 artifacts. The final model SHA-256 is
`2a13330687fda6a6fb90cf366ad70b0a963d549ef579579271d508db76aefeb1`.

Descriptive training blocks show no clear improving pattern:

| Training cases | Wins | Ties | Mean peak workers | Mean peak army supply | Mean kill reward | Mean collection reward |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 114000–114015 | 0 | 1 | 49.38 | 28.44 | .389375 | .133619 |
| 114016–114031 | 1 | 3 | 47.44 | 23.31 | .394375 | .126047 |
| 114032–114047 | 0 | 1 | 47.44 | 20.75 | .343531 | .128041 |
| 114048–114063 | 0 | 3 | 44.50 | 18.31 | .277219 | .117798 |

Reward columns are undiscounted sums of the respective intermediate terms only.
These blocks contain different cases; their trends are not matched causal
comparisons or frozen-policy strength measurements.

## Linux replay and resource use

Actual Medium Terran Air training victory 114024 was rendered on the installed
Linux SC2 build with its matching Simple64 map. The full export contains 742
frames at 4 fps, 185.5 video seconds covering 727.77 game seconds, at 640×480
H.264. No frame limit was reached. Rendering took 109.27 wall seconds; ffprobe
and a decoded frame verified the playable video and actual SC2 terrain,
structures, units and combat. The video depicts that training behavior before
the final update, not the final policy's Hard strength.

All artifacts are in the `Sam-v6/terran-rl` implementation worktree:
`logs/combined-combat-collection/` and
`logs/replay-proof/combined-reward-medium-terran-air-training-win.mp4`.
The training review is
`logs/audit/combined-combat-collection-training-complete-independent-review.json`.

Training's 786 sampled whole-machine CPU windows averaged 13.50% and peaked at
33.93%, under the user-authorized 80% ceiling. Shorter excursions are not bounded
by those samples. Jobs used four engines, eight allowed logical CPUs, nice +10
and CPU-only learning. Rendering ran after training ended, with one replay engine.
No installations, VM or sudo were needed.

## Frozen ordinary Hard comparison

All 24 paired games for cases 115000–115011 completed without infrastructure
failures, using both maps, all races and all five builds. An inference-only
adapter preserved actor choices while restoring ordinary combat scoring; no
harvesting credit influenced evaluation. No weights, optimizer state or RNG
changed during evaluation, and no training rollouts were collected.

| Policy | Wins / 12 | Defeats | Mean discounted combat return |
| --- | ---: | ---: | ---: |
| Retained parent | 4 | 8 | .214404 |
| Combined candidate | 0 | 12 | -.052778 |

Additional wins were -4 rather than the required +2; mean paired ordinary return
fell by .267182. Win gains were Terran -1, Protoss -2 and Zerg -1, so the positive
two-race requirement also failed. Parent victories 115003, 115004, 115005 and
115007 all became candidate defeats. No parent defeat became a candidate win.

The candidate produced some army in seven cases, with peak supply no greater
than 24. It produced none in 115001, 115003, 115005, 115007 and 115009. The parent
produced army in all twelve cases, peaking at 16–53 supply. The candidate's mean
undiscounted kill credit was .072917 versus the parent's .370000. These are
observations of actual play, not a proven causal account of the regression.

Independent complete review verified all 15,829 greedy decisions, ordinary
reward/discounted telescope calculations, journals, replays, case/role coverage,
checkpoint immutability and a separately reconstructed gate. Its receipt
`logs/audit/combined-combat-collection-hard-complete-independent-review.json`
binds 594 artifacts, including all 486 training artifacts. Review passed for
integrity while explicitly recording `hard_gate_passed:false`.

Hard evaluation's 193 sampled whole-machine CPU windows averaged 14.23% and
peaked at 24.54%. The retained production actor and reserved 50000–50029 final
acceptance bank remain unchanged. Intermediate kill feedback is physically
present, but this reward mixture did not improve macro strength. Future work
needs a distinct, separately declared mechanism rather than extending this arm.

## Advisory next mechanism

An authorized read-only Astra consultation checked the prior failures. The
[earlier unit-intent arm](2026-10-04-unit-intent-experiment.md) already tested
five-second choices with unit-only retries and failed all sixty frozen games.
It must not be described as an untried fix.

Astra recommends a capability/causality probe of longer resource-saving options:
eight fresh parent cases, one outcome-independently selected unaffordable target
per case with every other ordinary prerequisite satisfied, a commitment of at
most sixty seconds, and a matched wait-only control. Worker/combat micro stays
active; no prerequisite construction or build sequence is inferred. Issue the
chosen target once when feasible, or time out; then resume the parent. Maximum
24 games. Actual completed targets and gameplay benefit beyond matched waiting
would be required before proposing semi-Markov RL training.

This advice is not yet an implemented or accepted intervention. Withholding
spending may harm the economy or defense, and the parent may never create useful
prerequisites. Any subsequent variable-duration learner must preserve reward
accumulation, terminal events and elapsed-time discounting; changed affordability
masks are not an exact behavioral migration merely because weights match.
