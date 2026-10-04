# Combat event reward experiment

Direct Hard40 finite-win learning produced no training wins and the control
subsequently lost all six greedy and all six sampled frozen games. Full-return
potential shaping cancels: without wins, return targets contain the state
potential offset but no action-dependent successful-outcome signal. The trained
greedy control did not select production buildings. More exploration alone
has not established improvement.

The earlier combat-credit experiment added kill totals to a potential. This
experiment instead proposes actual counter increments as non-potential rewards.
That changes the objective and may favor combat or defensive trades over winning;
therefore keep it an explicit experiment and judge only real game victories.

1. Use archived finite/spatial initial actor, not failed Hard40 continuations.
   Keep observations/actions/micro/temperature 1/finite terminal convention and
   lambda 1 fixed. Retain the frozen initial greedy/sampled baselines.
2. Add `combat-events-v1`: each macro transition receives
   (increment killed unit + structure value - increment own lost mineral and
   vespene value) / 100 in unscaled reward, alongside the existing potential
   difference and true-win 100 payoff. Unchanged counters give zero event reward.
   Initialize previous counters at the first decision so pre-policy events are
   not attributed to an action. Record all components, including the final
   observed counter increment; do not fabricate unobserved terminal events.
3. Add tests for positive kills, negative losses, no recurring credit, correct
   transition attribution and finite terminal treatment. Check NumPy/Torch
   reward-context rejection. Explicitly migrate actor only with critic and Adam
   reset, recording source/parent/output hashes; no rollouts are carried forward.
4. Controlled engine evidence: combat-event-score-probe created Marines and
   weakened visible enemy units solely to validate counters. It recorded 132
   observations: killed units 150 to 950, structures 0 to 500, own loss value 0
   to 300; every counter was nondecreasing. This is a score API fixture, never
   training data or playing-strength evidence. Preserve its replay and JSON.
5. Separate train/resume/frozen smoke from untouched initial weights. Start a
   bounded Easy curriculum to obtain varied actual trades, then freeze both
   greedy and sampled development evaluations. Scale training only when receipts
   show valid event components and useful action exposure. Do not broaden to the
   reserved acceptance bank on weak development performance.

The archived event source now passes 80 tests. Three event path checks failed
before implementation; the return identity check includes a nonconstant critic.
Migration preserves the actor/shared weights and RNG/counters/gamma/cadence,
but resets the critic head, every Adam moment and optimizer step to zero in
both control and candidate. The historical parent update count remains in the
migration receipt, not as a stale Adam step. Initial actor logits match exactly
across 128 contexts; no rollout is carried forward. Control retains finite-win-v1,
candidate uses combat-events-v1, and candidate training rejects control context.

Additional engine fixtures validate valuation: a gas-bearing enemy kill produced
25 gas credit, with killed unit+structure values equal to killed minerals+gas on
every observed row. A separate own gas-bearing loss produced exactly 125 total
loss and 25 gas loss. These debug fixtures are neither RL data nor strength
evidence. Field semantics match Blizzard's score.proto:
https://github.com/Blizzard/s2client-proto/blob/master/s2clientprotocol/score.proto

Untouched migrated candidates live under logs/ppo-combat-events{,-control}/;
separate smoke copies live in logs/ppo-combat-events-smoke/. Source and migration
script are archived in logs/audit/ppo-combat-events-source/. A matched Easy40
comparison will use four workers per branch concurrently (eight engine clients
total), both maps, all three races, Rush/Timing/Power/Macro/Air builds, game limit
1200 seconds, macro cadence one second, same attempt/seed schedule. Preserve
first-batch actor parity until rewards differ, receipts and pre-batch weights.

The reliable Hard win-rate goal remains open.


Independent review verified 80 tests and migration arrays/hashes/context. Real
smoke train4 (120-second cutoffs), resume2 Hard (both defeats) and frozen sampled2
(120-second cutoffs) completed with zero failures; frozen bytes stayed identical.
The resume games contain 5 positive combat events and 96 negative events.
Every logged reward was recomputed from its recorded components successfully.
These demonstrate genuine score feedback and pipeline semantics, not improvement.
Untouched initial hashes were rechecked before copying the matched Easy40 parents.
Keep both archived sources frozen until their run handles are terminal.


First matched batch: seeds 111-114 produced one Victory and three cutoffs in both
branches. All 4,393 decisions have identical time/action/execution/legal/snapshot
traces across the branches, with matched opponent/context/game-time receipts.
Reward components differ by the intended event term. This proves initial behavior
parity and schedule matching before divergent learning, not reward improvement.
Receipt: logs/audit/combat-events-first-batch.json. Easy40 jobs remain running.


Paired Easy40 completed with zero failures: control 6 wins/14 defeats/20 cutoffs;
event 3 wins/15 defeats/22 cutoffs. All forty opponent/context schedules match.
The all-game audit verified monotonic counter attribution, recorded component
rewards, finite endpoint treatment and exact discounted-return identity including
events. Optimizer steps are 656 control/688 event (different trajectory lengths),
with 144 episodes/attempts each. This batch does not demonstrate improved strength.
Frozen greedy and sampled Hard6 checks for each checkpoint are now running;
keep acceptance seeds reserved. Artifacts: combat-events-easy40-results.json and
audit-combat-events.py under logs/audit/; frozen-easy40.npz under each branch.

A separate offline NumPy kernel benchmark found default threading faster than
forcing OPENBLAS_NUM_THREADS=1 (single-state median 0.036 vs 0.049 ms; batch of
512 states 7.4 vs 14.7 ms). These are local kernel timings during ongoing games,
not simulation throughput or a broad guarantee; they do not support changing
the current threading setting. No dependency was installed for this check.


All four frozen Hard6 runs completed with six defeats each, zero failures and
unchanged checkpoint hashes; schedules match. Control greedy army peaks were
22/16/9/27/23/28 and it selected Marine/attack commands. Net-event greedy army
peaks were zero in every game, with no Marines or attack selections. Both sampled
policies exercised some production but lost. This is a concrete loss of military
production, not simply too small a validation set. The net-event objective can
prefer cheap unarmed defeats over costly losing engagements; no continuation or
promotion of this candidate is justified by current behavior. Preserve control
and candidate independently. Results: logs/audit/combat-events-hard6-results.json.

Independent review checked all 83,203 Easy transitions and full returns from
every decision (maximum identity error 1.41e-14). Candidate training exposure had
1,661 positive and 2,622 negative event increments. Event wins by ten-game blocks
were 1/0/1/1, versus control 1/2/1/2; the event hypothesis is not scientifically
rejected, but no strength improvement has been demonstrated.

Next investigate the direct proxy incentive: a kills-only increment rewards
combat without charging own deaths (retain losses as diagnostics). Keep the same
initial actor, reset control and all other context for a bounded comparison; do
not simultaneously alter micro/representation/temperature/cadence. Separately,
full-return potential shaping gives a state-only return offset; a zero reset
critic has not yet learned that offset. An analytic potential baseline or removal
of potential shaping could reduce that variance without changing the win/event
objective, but that is a separate intervention requiring its own tests/control.
Neither change is implemented yet.


Replay proof: logs/replay-proof/combat-event-hard-loss.mp4 is a complete rendered
Terran Rush Hard defeat from this net-event greedy checkpoint (seed 10000):
416 frames, 960x720, 4 fps, 104 video seconds covering 406.79 game seconds.
Exporter completed without frame cutoff; ffprobe verified duration/frames and a
late frame was inspected. Omniscience is for replay viewing only.

Review supports the isolated kills-only countermeasure, leaving the potential
estimator unchanged. The new source lives in logs/audit/ppo-combat-kills-source/.
Two tests failed before removing the loss term; losses remain in component logs.
It will use the same untouched zero-critic/zero-optimizer/RNG/counter initial
state as the already completed net-event comparison. Reuse that recorded net
control, retaining hashes/schedules, rather than silently rerunning or replacing
it. Validate initial traces before comparing diverged outcomes. Neither candidate
is promoted without real frozen Hard improvement.
