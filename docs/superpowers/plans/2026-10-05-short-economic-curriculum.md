# Short economic curriculum

Goal: test whether RL can improve economic decisions with nearer-term credit,
then immediately test transfer to ordinary Hard games. This is auxiliary
training, not a replacement for victory or reliable Hard acceptance. The last
[Hard discovery arm](2026-10-05-hard-counterfactual-discovery-results.md) remains
closed. No labels from that arm or earlier validation banks enter this fit.

User-authorized Astra consultation recommends this mechanism after economic
forgetting and scarce successful exploration. In the closed Hard discovery,
36/47 alternatives were wait, retreat or attack; none selected SCV or Marine.
That result does not establish observation aliasing. The curriculum changes
the objective and credit horizon together as one explicit task migration; it
does not add observations, scripted macro or an optimizer tournament.

## Accounting gate before training

Use the engine's score counters, not reconstructed surviving wealth:
E = (collected minerals + collected gas - initial collected counters)
minus (recorded lost minerals + lost gas - initial loss counters).
Sum loss fields over none, army, economy, technology and upgrade. Call this
net collected resources less recorded losses; do not claim conserved wealth.
Subtract the initial counter readings, not starting banked resources.

Installed BurnySC2 exposes these counters directly, but its wrapper does not
certify mining, spending, cancellation or morph semantics. Before curriculum
games, implement synthetic accounting tests and an isolated engine capability
fixture, at most four games. Verify mining increases collection, ordinary
spending/cancellation/morphing creates no positive collection or loss credit,
and actual destruction records resource loss once. Account for frame delay and
retained initial counters explicitly. Do not infer loss semantics from a debug
removal if it bypasses ordinary death accounting. Any debug setup belongs only
to this labelled capability fixture, never training/evaluation.

Freeze fixture source and operations before running it; retain all observations
and failures. Stop this proposed objective if accounting cannot be validated
within the fixture budget. No silent counter substitution or approximation.

## One fixed task migration

Copy immutable parent 0f3e05d9efd5eba4fd238a6282e462599ffc675f008b98fd42925e99f6bb16c6.
Preserve actor/body parameters and original 5460 live features,27 actions,
one-second cadence and executor/micro. No worker quota, build order, composition,
attack schedule or state-selected exploratory action. Preserve parent provenance
and lifetime counters separately from this task's optimizer age.

Reset the value head to zero, all Adam moments and optimizer age together.
Use gamma=1,lambda=1 for this finite task; retain other existing PPO settings.
Pay only E/1000 at termination, with no victory, kill or potential reward.
Record a distinct reward version and explicit scale. The critic reset addresses
objective mismatch; it does not guarantee against economic collapse. Verify
initial actor probabilities and greedy choices exactly reproduce the parent.
The task uses an isolated .001 reward-scale context, not a silent change to the
production ActorCritic loader's .01 contract. Set task updates=0 (the PPO helper's
Adam clock), episodes=0 and attempts=0, and clear rollouts. Keep the parent's
676 updates and144 lifetime episodes/attempts in a separate provenance record.

Train exactly32 episodes,300 game seconds each, against VeryEasy computers.
Freeze exact fresh seed assignments cycling three races, five builds and two
maps before any cases run, with separate training and evaluation banks. Use
ordinary resources and fog. Sample the learned categorical policy; update in
batches of four complete trajectories with the verified PPO helper. Keep final
checkpoint only; no early checkpoint selection, restart, added episodes or
parameter sweep. A death before300 seconds terminates normally with measured E;
retain its result rather than replacing it. Failed processes remain receipts
and prevent complete-coverage claims.

## Separate learning and transfer gates

Evaluate parent and final candidate greedily on eight separate, precommitted
300-second VeryEasy cases (16 games). Require complete valid coverage, mean E
gain at least max(100 resources,5% of absolute parent mean E), and positive mean
gain in at least two races. Report all losses/regressions and worker/production
behavior descriptively. No economic gate means no Hard games or extension.

Only if economic improvement passes, freeze candidate and run12 fresh paired
Hard cases (24 games), four per race, both maps and all five builds. Keep the
original full-game limits/reward and greedy evaluation; curriculum critic is
irrelevant to frozen action selection. Require at least two additional wins,
nonlower mean ordinary discounted return and positive win gains in two races.
Report every regression and paired uncertainty. No fitting against either
evaluation bank. A transfer failure closes this curriculum, even if its economic
score improves. A pass is not the reserved70% Hard acceptance result.
Use an explicit evaluation-only adapter that preserves all actor/body parameters
while restoring the ordinary combat reward context, .01 scale and parent gamma
.9979919516614258. It cannot collect training rollouts or save a resumable PPO
checkpoint. Verify actor logits/probabilities/greedy choices remain exact under
this adapter; never mislabel the curriculum optimizer state as combat training.

Maximum76 engine games including four accounting fixtures:32 training,16
economic evaluation and conditional24 Hard transfer. Use at most four engines,
the eight-CPU nice+10 CPU-only wrapper, sampled40% whole-machine CPU guard and
owned-job cancellation. Preserve all traces, replays, checkpoint snapshots,
source/input hashes and optimizer receipts in a new ignored experiment root.
Reserved50000 and existing development banks remain untouched.

Implementation/source tests, immutable case banks and independent review precede
each live phase. This document authorizes no unreviewed implementation or games;
the user's overall autonomous authorization remains in effect.
