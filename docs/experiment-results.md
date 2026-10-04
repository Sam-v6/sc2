# Local experiment results — 2026-10-04

All results below are development experiments, not final acceptance. Replays,
action observations, checkpoint snapshots and JSON receipts are retained under
`logs/` in `.worktrees/terran-rl`. A first frozen Hard victory is established; reliable all-race Hard strength is not.
The final target remains frozen evaluation against all three races and varied
builds/maps, using a fresh seed bank after development choices are finished.

## Infrastructure evidence

- Real 120-second training smoke games produced updates, saved checkpoints and
  nonempty replays. Resuming preserved the optimizer, replay experience and RNG.
- Frozen evaluation left the checkpoint SHA-256 unchanged. A forced one-second
  wall timeout also left the canonical checkpoint unchanged.
- Linux replay rendering used the already installed SC2 4.10 build 75689,
  OSMesa and ffmpeg. A learned-agent replay exported 124 frames at 640x480;
  the 31-second MP4 represents 120 game seconds at four frames per second.
- The current unit suite includes command ordering, replay terminal observations,
  encoder error preservation and early-failure receipt regressions.

## Initial five-second macro experiment

| Run | Completed / requested | Wins | Losses | Cutoffs | Failures |
| --- | ---: | ---: | ---: | ---: | ---: |
| Hard training | 20 / 20 | 0 | 20 | 0 | 0 |
| Frozen Hard development evaluation | 6 / 6 | 0 | 6 | 0 | 0 |
| Random Hard comparison | 6 / 6 | 0 | 6 | 0 | 0 |
| VeryEasy curriculum, manually interrupted for repair | 13 / 20 | 10 | 1 | 2 | 0 |

The six-game comparisons use Simple64, Rush and Macro builds, all three races,
and seeds 10000–10005. The learned checkpoint after Hard training has SHA-256
`f94113376c30151f2ea357874111c936da54527ff46753adeb28f8020fc3aa0c`.
Both frozen and random comparisons preserved that checkpoint. The three scripted
Hard losses in `performance-baseline.md` used a different seed/build setup and
are not a matched comparison to these runs.

Review found a primitive bug: worker redistribution ran after macro construction
and could issue a gather command to the newly selected builder, canceling its
build order. Some traces logged a command as issued without the expected resource
expenditure or pending structure at the next observation. These data remain useful
for debugging, but do not represent the repaired executor. Gathering now runs
before macro decisions; a regression test reproduces the old ordering failure.

The frozen policy also rarely trained workers and built excessive infrastructure.
Five seconds per atomic action limited production. The next experiment starts a
fresh checkpoint with repaired command ordering and one-second macro decisions,
beginning with easier opponents. Its live feature representation and action space
are still explicitly experimental. None of these changes scripts a build order
or chooses an army mix on the policy's behalf.

## Representation limits

Visible enemy counts and distances are observed during play, but the compact
encoder loses unit identities, terrain and detailed positions. This is not the
end state requested by the user. Broader perception should be evaluated after
this first experiment establishes a reliable learning and replay workflow.

## Repaired executor and learning diagnostics

The fresh one-second, gamma .99 v2 batch completed 20 VeryEasy games: 16 wins,
1 loss, 3 cutoffs, no failures. An early frozen development snapshot lost all six
VeryEasy games by repeatedly choosing wait; exploratory training wins were not
reliable greedy-policy strength. The separate gamma .998 v3 batch completed
20 VeryEasy games: 16 wins and 4 cutoffs, no failures.

A controlled offline probe trained 32-step returns and masked Double-DQN from an
eight-game v3 snapshot: frozen VeryEasy evaluation yielded 4 wins and 2 cutoffs;
frozen Hard evaluation yielded 6 losses. These probes use development seeds
10000–10005, Simple64, Rush/Macro, all three races. Their buffers are diagnostic
artifacts and explicitly cannot be resumed with the earlier one-step trainer.

The current trainer uses up to 32 decision rewards, records the actual bootstrap
discount, and uses online action selection with target-network valuation. Version 2
checkpoints retain these discounts and load version 1 experience as one-step.
Partial cutoff horizons bootstrap; terminal horizons stop. For a new checkpoint,
gamma=.99**(macro_seconds/5) preserves the initial physical discount horizon.
Uncorrected long returns include exploratory continuation; frozen evaluation must
check whether this credits waiting for later exploratory actions.

A learned exploratory VeryEasy Terran win exported fully: 512 frames, 501.79 game
seconds, 128-second MP4. The viewed frame shows excessive infrastructure, reinforcing
that easy wins alone do not establish useful macro strategy or Hard strength.

## Spatial primitives and parallel collection

Independent review traced one frozen game to 357 failed expansions out of 358
selections, and another to repeated queued tech-lab commands without construction.
Expansion now requires an eligible builder, a reachable and placeable destination;
execution uses that same builder/destination. Add-on choices use feasible producers,
and later construction preserves vacant add-on footprints. These are execution
constraints, not a prescribed expansion timing or technology strategy.

The earlier Easy curriculum finished 30 games: 17 wins, 4 losses, 9 cutoffs. The repaired
v5 Medium batch finished 40 games: 8 wins, 25 losses, 7 cutoffs, no engine failures.
Its starting and post-Medium frozen Hard evaluations each lost six games.
Replay experience from the earlier spatial defects was cleared while retaining
weights/target/optimizer/RNG; that migration is recorded in `logs/learning-v5/`.

The current trainer collects four games per behavior snapshot, then the parent
learns from successful episode samples in launch order. Worker models never
replace newer parent weights. 46 unit tests pass, including mixed-failure schedule
resume and cancellation. Real short collection measured 3.39x throughput with four
workers; details are in performance-baseline.md. A real four-engine interruption
preserved the canonical checkpoint, removed candidate saves and left no descendants.

## First frozen Hard victory

A separate frozen-only economic-capacity shaping probe replayed the same 20-game
v3 observation buffer, using 32-step returns and 10000 Double-DQN updates from fresh
seed 19 weights. Its potential is:

`max(0, .5*workers + .2*army_supply + 2*bases - .002*resource_bank)`

Resource bank uses the encoder's clipped mineral/gas values; terminal results
remain +100/-100. There is no scripted macro build order or army mix. This diagnostic
checkpoint must not resume under the trainer's older reward potential.

Frozen Hard evaluation on the reused development bank won 1/6 games, with 5 terminal
losses and no failures. The win was Terran versus Hard Protoss Rush, Simple64,
seed 10001, 851.79 game seconds. The selected actions included 44 SCVs and 44 marine
commands; peak observed workforce 54, army supply 47, marines 30. Evaluation performed
no updates; SHA-256 before/after remained:
`5b335bde6c0593980cbdd0139f40d8362af8f9babb4a49996e25000ac3446251`.

The descriptive Wilson 95% interval for 1/6 is approximately 3%–56%; these seeds have
been used for development selection, so fresh holdout evaluation is still required.
One victory does not meet the all-race/reliable Hard target. Raw evidence is in
`logs/economy-hard-eval/`, the frozen probe and its objective receipt in
`logs/economy-probe/`, and the probe script in `logs/audit/economy-potential-probe.py`.

## Broader Hard training

The repaired v5 policy completed 100 Hard training games across Rush, Timing,
Power, Macro and Air builds: 5 wins, 90 losses and 5 cutoffs, with no engine
failures. Exploratory victories included Terran and Zerg opponents. A frozen
snapshot after 72 games lost all six development evaluations; training wins
therefore did not establish dependable greedy-policy strength. The batch took
1088.97 wall seconds for 78083.21 simulated game seconds across four workers.

The first frozen Hard victory is watchable in
`logs/replay-proof/first-hard-win.mp4`: 869 frames at 960x720, 217.25 video
seconds representing the full 851.79-second game. Its export receipt confirms
that the frame limit did not truncate the replay.

## Reward probes and next learning correction

The economic probe's separate 30-game development evaluation used Simple64 and
TritonLE, all three races and Rush/Timing/Power/Macro/Air, seeds 20000–20029.
It earned 1 victory (Zerg Rush, Simple64), 28 defeats and 1 cutoff, no failures;
its checkpoint hash remained unchanged. The eight-step version of that probe
lost all six initial development games. These results do not meet the target.

Removing the stockpile penalty while retaining the same capacity coefficients,
source corpus, seed 19 initialization, gamma and 10000 updates yielded 1 victory,
4 defeats and 1 cutoff in the original six-game bank. The win was against Hard
Terran Macro, Simple64 seed 10003, 657.86 game seconds. Checkpoint SHA-256 remained
`47f49791f07d484adc93d794ea61c9666435ae97d5a4ff093f3ea246ad23017e`.
Frozen victories now exist against each race across these separate reward probes;
there is still no single reliably strong policy. A 30-game capacity evaluation
uses an archived copy of the old source under `logs/audit/capacity-eval-source/`
so its schema and source hashes remain stable during further development.

Review found eight successive attack/retreat choices with army supply 4 and no
visible enemies, while the old encoder could not distinguish army travel from
standing near home. The next encoder adds distance from home, distance from known
enemy spawn, and time since the last stance change. It retains policy control
of attack/retreat and imposes no attack timing recipe.

The collector now truncates a return before a later action differs from the
frozen worker's legal greedy action, avoiding direct credit for a nongreedy
continuation's reward. This is inspired by trace cutting in
[off-policy return methods](https://arxiv.org/html/1606.02647v2).
It reduces collection-time exploration contamination; it is not an exact
correction after subsequent parent-weight updates, nor a convergence guarantee
for this neural approximation.

The current `capacity-v1` reward objective is recorded in checkpoints and required
for training resume. Its potential is `.5*workers + .2*army_supply + 2*bases`, using
encoder caps; spending without capacity growth does not earn positive shaping.
The recorded v6 migration retains the capacity probe's learned weights, target,
Adam and RNG, appends zero input rows for the new features, and clears old replay
experience whose positional features are missing. It does not relabel data with
invented positions. Four real migrated 180-second smoke games completed with
four cutoffs, saved replays and policy updates, no failures. 51 unit tests pass.
A numerical equality check in the first migration attempt differed by less than
2e-15 after zero-row padding; a tolerance-based check replaced exact equality.
The unintended fresh-model smoke run from that attempt is retained separately
under `logs/learning-v6-fresh-smoke/` and is excluded from strength comparisons.

The capacity probe's broader 30-game check earned 1 victory (Zerg Power, Simple64),
27 defeats and 2 cutoffs, no failures. Its hash remained unchanged. The separate
six-game paired combat-interface test used the same frozen v6 checkpoint and
seeds 31000–31005, with source snapshots preserving each interface. Both the
original stance-change interface and the idempotent hold-stance variant lost all
six games. The variant therefore remains a diagnostic source snapshot; it was
not promoted into the trainer. Unavailable-action Q extrapolation does not prove
that the original mask is wrong, because wait already preserves the stance.

A normalized capacity probe used one-step returns, the same old v3 corpus,
seed 19 and 10000 updates, with all capacity/terminal rewards multiplied by .01.
It lost all six original development evaluations. Its objective differs from
the current trainer, so it is retained for frozen evaluation only. This did not
provide evidence to promote reward normalization or change the trainer again.

## Completed v6 batch and PPO workflow comparison

The v6 DQN experiment ultimately completed 60 valid Hard games: 2 victories,
57 defeats and 1 cutoff. One additional attempt disconnected during engine
startup, was excluded from training, and was retried; the remaining games then
completed. Its separate frozen 30-game development evaluation (seeds 32000–32029,
both maps, all races and five builds) earned 1 victory, 28 defeats and 1 cutoff,
no failures. SHA-256 remained
`ea8bcf9825766d4f2ce0b6f62fe433f6998d28ed15fca6aa29a308b0da80515b`.
The broader strength target remains unmet.

An existing PyTorch 2.7.1 CPU-capable runtime was found in the sibling SC2RL
Python 3.11 environment. The new bounded PPO comparison keeps NumPy inference in
Python 3.12 game workers and invokes that existing runtime only for gradients.
It does not install Torch or reuse the old Protoss model. Actor/critic inference,
masked probabilities/log probabilities, episode-boundary GAE, clipping, Adam
resume, RNG, schema and reward scale have explicit checks. One update uses the
whole collection batch; valid frozen behavior probabilities are retained.

The first real PPO smoke completed four games but exposed a launch-path bug:
resolving the virtualenv Python symlink selected the base interpreter without
Torch. The learner failed without changing the canonical checkpoint; its
trajectories were discarded. A trainer-level regression reproduced that failure.
The corrected launcher preserves the interpreter path and original helper stderr.
Four repeated real 180-second smoke games then completed with no failures, valid
replays and policy updates. Their cutoff ties are infrastructure evidence only.
The local suite now passes 58 tests, including real CPU Torch learning/optimizer
resume and fail-closed helper behavior.

PPO resume then completed 20 full VeryEasy games: 20 wins, no cutoffs or failures.
The initial frozen two-game 180-second Hard smoke produced two cutoffs and left
its checkpoint unchanged. The subsequent full frozen Hard check (all three races, Rush and Macro on
Simple64, development seeds 10000–10005) lost all six games, with valid replays
and no failures. Its checkpoint stayed unchanged. Easier training wins do not
establish greedy-policy strength. A broader Medium curriculum run follows;
these are development experiments, not the reserved acceptance seed bank.

PPO's subsequent 40-game Medium curriculum (Simple64/TritonLE, all races and
five builds) completed with 2 victories, 29 defeats and 9 cutoffs, no failures.
The two victories are sampled training results. The saved post-Medium snapshot
is being checked separately with greedy inference and seeded categorical
sampling on the same six Hard development matchups. The sampled probe preserves
an archived source copy and explicit changes; it does not replace the greedy
protocol. A bounded 120-game Hard training batch then resumes the canonical PPO
checkpoint across both maps and all five builds.

The paired six-game post-Medium checks finished: greedy PPO earned 1 victory,
4 defeats and 1 cutoff; categorical sampling lost all 6. Neither had failures
or changed the frozen snapshot (SHA-256
`4219cc29117ba39d067732cffdf34b22bbeb9cf175f70aec1b1ded350a695af4`).
The greedy victory was Protoss/Rush on Simple64, seed 10001, lasting
896.79 game seconds (`fddcc961b01b40ceb0ae2f38080c48eb`). A broader
30-game greedy development evaluation uses seeds 34000–34029 and both maps.
The initial 12 Hard PPO training games were all losses.

## Paired longer-credit probe

Read-only review found no sampling, reward-sign, GAE-boundary or gradient bug.
The actor remained weakly discriminative: on the greedy winning Hard seed10001,
initial SCV probability was .518 versus wait .482; some later attack choices were
also about .51/.49. Categorical sampling can delay those slightly favored actions.
With one-second decisions (actual 1.071 seconds), gamma≈.998 and lambda=.95 give
the direct GAE contribution a roughly 13.9-game-second half-life. Longer credit
therefore depends on critic bootstrap estimates. Across six sampled Hard losses,
the initial critic estimate was -.0422 versus realized discounted shaped returns
-.2547 to -.4267. These outcomes suggest optimism on Hard, not a proven expected
value error. Discounted capacity-shaping telescoping identities held to ≈1e-15.

A separately archived source probe changes only GAE lambda from .95 to .99.
It starts from the exact post-Medium network, Adam state, RNG, attempt cursor,
reward, cadence and action schema. Its first 40 Hard matchups match the baseline
batch's first 40 seeds/maps/races/builds. The source and explicit checkpoint
metadata migration are retained in `logs/audit/ppo-long-trace-source/` and
`logs/audit/ppo-long-trace-probe.py`, with SHA-256 provenance. The baseline source
and canonical model are unchanged. Because settings are validated, this candidate
must use its matching archived source for inference or resume. This is an
algorithm experiment, not a correctness repair or a production-default change.

The post-Medium frozen 30-game development evaluation completed with 2 victories,
17 defeats and 11 cutoffs, no failures; its checkpoint stayed unchanged. The
victories were Zerg/Rush and Protoss/Rush on Simple64 (seeds 34002 and 34001).
There were no victories on TritonLE or against Terran in this batch. The 11
cutoffs are not wins. This candidate does not meet the acceptance target.

The paired 40-game training comparison finished: baseline 0 wins/39 losses/1
cutoff; longer trace 0 wins/38 losses/2 cutoffs. Both schedules matched exactly,
and the first four games had identical chosen actions/times before any updates
differed. Evidence is retained in `logs/audit/ppo-long-trace-pairing.json`. This
does not justify promoting the longer trace; its frozen test follows. Meanwhile
a separate original-settings curriculum resumes the preserved post-Medium model
for 200 Easy games, eight workers, five 40-game stages with retained snapshots.
It aims to collect more winning trajectories before revisiting Hard. Easy wins
remain training evidence only; all races, builds and both maps stay in scope.

The longer-trace frozen six-game test lost all six; this variant was not
promoted. The original-settings Easy curriculum's first 40 games produced 1
win, 3 losses and 36 cutoffs. Sampled traces showed median stance dwell ≈2.14
seconds. In one TritonLE cutoff (seed 92), peak army supply was 87, while the
army center never got closer than 132.87 to the enemy spawn from an initial
152.79 distance. This is evidence of limited travel, not proof that no individual
unit reached the enemy.

A separate action-interface probe keeps a chosen stance for at least 30 seconds
while economy decisions still occur every second. It starts from the same
post-Medium snapshot, with 40 Easy matchups/eight workers matching the curriculum
first stage. The archived source is `logs/audit/ppo-stance-source/`; three checks
verify both stances, the exact 30-second boundary, and unchanged economy-action
availability. This temporarily restricts retreat responsiveness and is only a
controlled temporal-exploration experiment. No scripted build order or unit mix
is added. Matching archived execution is required for evaluation.

The original-settings 120-game Hard PPO batch completed with 1 victory, 110
defeats and 9 cutoffs, no failures (2436.782 wall seconds). Its training victory
was Terran/Power on Simple64, seed 163, 892.86 game seconds
(`d06ddd8480704de1bb4c1973d2822f6e`). The final frozen snapshot is
`logs/ppo-v1/frozen-after-hard120.npz`, SHA-256
`476f09ade238e6a1d27caccf50d9b59be6f825837da915f4fc100c88e1a36d73`;
its frozen evaluation is still pending. An earlier snapshot after 56 Hard games
lost all six frozen development matchups.

The frozen post-Medium PPO Hard Protoss/Rush win was exported locally as
`logs/replay-proof/ppo-hard-win.mp4`: 915 frames at 960×720, 4 fps, 228.75 video
seconds,≈897 game seconds, no frame cap. ffprobe verified the MP4 and a late
frame was inspected. Replay viewing removes fog; training remains limited to
observed enemy units. The game receipt establishes Victory; the replay export
receipt's null result alone is not win evidence.

The 30-second stance probe completed 40 Easy games: 4 wins, 18 losses, 18 cutoffs,
no failures, versus 1/3/36 in the matched unrestricted first stage. The 40
seed/race/build/map schedules match; both used eight workers and the same
initial checkpoint. Its frozen six-game Hard test lost all six. The final
original-settings 120-Hard-game snapshot also lost all six frozen tests.
Neither candidate was promoted. A separately labeled unrestricted-execution
transfer check evaluates the stance-trained weights without the 30-second
constraint; it does not replace the matched-context result.

The unrestricted execution transfer of the stance-trained model also lost all
six Hard cases, with no failures. The original Easy curriculum finished all 200
games: 19 wins, 20 losses, 161 cutoffs, no failures. Per-40-game stages were
1/3/36, 0/5/35, 0/2/38, 10/6/24 and 8/4/28 (wins/losses/cutoffs). Each stage's
model is retained in `logs/ppo-easy-curriculum/frozen-easy{40,80,120,160,200}.npz`.
The 160- and 200-game models each lost all six frozen Hard development cases,
with no failures and unchanged checkpoint hashes (`logs/ppo-easy160-frozen/`,
`logs/ppo-easy200-frozen/`). These results do not establish curriculum improvement
or justify promoting either checkpoint.

The trainer now retains the exact behavior checkpoint per training batch.
Real DQN and PPO short train/resume/evaluate tests succeeded, including receipt
hash checks, six-episode resume state and unchanged frozen checkpoints. All were
120-second cutoffs and are infrastructure checks, not strength evidence.

The live composition correction appends Reaper, Hellion/Hellbat and Viking
fighter/assault counts without changing reward, action or learner settings.
Before the fix, equal-supply five-Hellion and five-Viking armies encoded identically.
A recorded zero-input-row warm start preserved old outputs and optimizer/RNG
state. All 63 tests and an independent review pass; real train/resume/frozen
120-second smoke games had no failures and preserved frozen checkpoint bytes.

The matched 40-game Easy composition comparison produced 1 win, 3 losses and
36 cutoffs, no failures. All schedules matched the previous first-stage control,
and all first-eight frozen-policy games had identical chosen actions/times.
Thirty-nine of 40 outcomes and game durations matched. The new features were
actually exercised (peak Reapers 48, Hellions 16, Vikings 1), but this run did not
show a strength improvement. Its preserved snapshot then lost all six frozen
Hard development cases, no failures and unchanged hash. Artifacts are in the
`terran-training-history` worktree's `logs/ppo-composition-curriculum/` and
`logs/ppo-composition-hard6/`. The schema correction remains useful independently
of a training-strength claim. Matching pre-composition source for old models is
retained in `logs/audit/ppo-pre-composition-source/`.

A separate archived-source probe jointly adds observed destroyed-asset score
features and potential shaping. The mathematical tests, metadata guards and
65-test archived suite pass. It starts from retained pre-smoke bytes, so its
40-game schedule and initial actor match the composition control; its change
is both observation and reward, not a reward-only intervention. See
`docs/superpowers/plans/2026-10-04-combat-credit-probe.md`. No default reward or
strength acceptance criterion is changed.

The combat-credit comparison completed 40 Easy games: 1 win, 7 losses, 32
cutoffs, no failures, versus the composition control's 1/3/36. All 40 schedules
match, and the first eight frozen-input games chose identical actions at identical
times. Observed kill counters were exercised (peak unit value 13,400, structure
value 5,925), though the potential clips each at 10,000. An independent native
asset-destruction probe also confirmed nonzero engine unit and structure counters
(950 and 500). The debug-spawned-building diagnostic yielded zero structure
value, so that earlier diagnostic alone did not establish the structure signal.
Pairing evidence is retained in `logs/audit/ppo-combat-pairing.json`; the native
API diagnostic is `logs/audit/score-probe-native.json`. No strength improvement
is established; frozen Hard evaluation is pending. This remains an archived
combined-observation/reward probe rather than the default objective.

The verified workflow has been integrated into the original checkout. Its
existing Python environment passed all 63 tests and two real DQN training games
completed with 224 updates, two episodes/attempts and no failures. Both were
120-second cutoffs, so these are delivery checks only (`logs/delivery-smoke/`).

The combat-credit snapshot lost all six frozen Hard development games with no
failures and an unchanged checkpoint hash (`logs/ppo-combat-hard6/`). It is not
promoted. Extra destruction feedback did not establish a strength gain in this
bounded comparison; a broader evaluation would not rescue the six-case failure
as a success claim. The default objective remains capacity-v1.

After vector normalization was integrated, the original checkout resumed for two
more real games without failures, advancing to four episodes/four attempts/448
updates. Two frozen games then completed without failures, preserved checkpoint
bytes, and produced nonempty replays with matching receipt model hashes. All six
delivery games are 120-second cutoffs and are infrastructure evidence only.
The original checkout's existing environment and the worktree environment each
passed 63 tests; experimental matching sources and replay/model artifacts remain
retained in their original worktrees. The reliable all-race Hard target remains
unmet and the goal remains active.

The detector-capability experiment completed 40 matched Easy games with one win,
eight losses and 31 cutoffs, without failures. The policy issued Raven production
22 times and turret construction 551 times; these counts describe issued commands.
Live observations reached three Ravens, 19 completed turrets and three observed
cloaked enemy units. Frozen Hard development evaluation then produced zero wins,
five losses and one cutoff, without failures or checkpoint mutation. Detection
execution works in controlled engine fixtures, but this comparison establishes no
strength gain. The combined detector action/observation/support-micro candidate
is retained separately and is not promoted. See `logs/ppo-detection-curriculum/`,
`logs/ppo-detection-hard6/` and `logs/audit/ppo-detection-pairing.json`.

A separate finite-match objective experiment treats normal game-limit ties as
learning endpoints, gives only true wins a terminal payoff, and uses complete
discounted returns (GAE lambda 1). Runtime failures remain failures. Live match
limit/remaining-time inputs make the horizon observable. Migration preserves the
actor, shared parameters, optimizer history and RNG, appends zero input rows and
resets the critic head/moments for the changed target. This jointly changes
payoff, endpoint treatment, credit horizon and horizon observations; it is not
a proven bootstrap bug or a controlled single-factor intervention.

All 68 archived tests pass, including finite-outcome and telescoping-return
checks. Real training (four games), resume (two) and frozen evaluation (two)
completed without failures; all eight were 120-second cutoffs. Training advanced
the inherited counters to 70 episodes/attempts and 812 updates; frozen evaluation
preserved checkpoint bytes. An independent review confirmed the return identity
and migration arrays/moments/RNG/hashes. The 40-game comparison starts from the
untouched migrated initial checkpoint, separately from these smoke models.
Artifacts: `logs/audit/ppo-finite-win-source/`, `logs/ppo-finite-win/`,
`logs/ppo-finite-win-smoke/` and `logs/ppo-finite-win-paired/`. Results are pending.
The first attempted curriculum used an incorrect build order, was interrupted
with 24 completed receipts (six losses/18 cutoffs), and is excluded from paired
strength comparisons. The reviewer identified this confound and independently
verified actor probability/action parity on 16,596 logged decisions. A restart
whose initial-copy preparation failed was stopped before any game completed;
its fresh model is also excluded. Both partial directories are retained for audit.
The paired restart explicitly uses Rush/Timing/Power/Macro/Air and untouched
migrated initial bytes; no parameters from excluded runs are reused.

The corrected finite-match curriculum completed 40 games with four wins, 14 losses
and 22 cutoffs, without failures, versus detector-control 1/8/31. Every opponent
seed/map/race/build/cadence matches, and the first eight pre-update games have
identical sampled actions/times. Later policy seeds can diverge because PPO
shuffling consumes parent RNG according to rollout length. The pairing receipt
is `logs/audit/ppo-finite-win-pairing.json`. Frozen Hard6 then produced one win,
four losses and one cutoff, without failures and with unchanged checkpoint bytes.
The win was Zerg Rush, seed 10002, 672.5 game seconds. This is an isolated learned
win, not reliable all-race Hard strength. A retained frozen snapshot now runs a
30-game development evaluation covering both maps/all five fixed builds, seed
20000; the fresh acceptance bank remains reserved.

An observation-only experiment now adds protocol type counts and observed unit
health/shields/capabilities/positions on an eight-by-eight map grid. Its reward,
actions, micro and learner settings match the detector initial control. All 69
tests pass; an independent review verified input order/scales, sparse JSON
reconstruction, fog-respecting source lists, and parameter/moment/RNG migration.
Actor/critic/probability parity is exact over 128 recorded live observations.
Type and position are aggregated separately, and scouted snapshots can be stale;
this remains an intermediate perception experiment. Dense training observations
for eight full games alone take about 373 MiB before additional copies.

Real unit-state train4/resume2/frozen2 smoke games completed without failures,
all 120-second cutoffs. Frozen bytes are unchanged and all replays are nonempty.
A controlled two-client engine fixture exercised observed cloaked enemies, Raven
and turret types, health, capability and spatial inputs (`unit-observation-production.json`).
An earlier copied production fixture failed its add-on placement command; that
failed receipt is retained separately. The revised fixture injects observed units
to test encoding only and establishes no production or strength claim. A 40-game
unit-state curriculum starts from untouched migrated input bytes. Artifact roots:
`logs/ppo-unit-state/`, `logs/ppo-unit-state-smoke/`,
`logs/ppo-unit-state-curriculum/`, `logs/audit/ppo-unit-state-source/`.

The finite-match Zerg Rush win has a complete local Linux MP4 at
`logs/replay-proof/finite-hard-zerg-win.mp4`: 686 frames, 960x720, 4 fps, 171.5 video
seconds, covering 672.77 game seconds without a frame cutoff. Export completed,
ffprobe confirmed the media, and a late frame was visually inspected. Replay
viewing is omniscient; the training policy receives only SC2-observed information.
The exporter result is null; the game receipt, not that null value, proves Victory.

The first full-length unit-state PPO batch collected 8,239 samples and completed
its CPU helper update in 3.94 seconds, within its 120-second supervision limit.
A later live Linux memory snapshot reported parent high-water 916,316 KiB and
active Python game workers around 187,000 KiB each. This snapshot is not the total
job memory peak. Concurrent Hard evaluation and replay rendering mean these
wall timings are not a controlled throughput comparison. Receipts:
`logs/audit/unit-state-memory.json` and `unit-state-benchmark.json`.

The finite-match frozen30 development evaluation finished with two wins, 19 losses
and nine cutoffs, no failures and unchanged checkpoint bytes. This fails the
reliable all-race Hard target; neither isolated wins nor smoke checks establish
acceptance. The candidate remains separately retained, not the default objective.
Artifacts are `logs/ppo-finite-win-hard30/`; seed 20000 is a development bank.

The unit-state Easy40 comparison finished with two wins, 14 losses and 24 cutoffs,
without failures, versus detector control 1/8/31. All 40 opponent schedules match
and the first eight games have identical actions/times/policy seeds. Its five
full-game PPO helpers each completed within 5.22 seconds (8,037–8,968 samples); no
learner limit or memory failure occurred. The 40 games took 507.36 wall seconds with
other evaluation/rendering jobs running, so this is not controlled throughput.
Its immutable frozen snapshot now runs six Hard development cases. No strength
gain is established and the main compact experiment remains the default.
Artifacts: `logs/audit/ppo-unit-state-pairing.json`,
`logs/ppo-unit-state-curriculum/`, `logs/ppo-unit-state-hard6/`.

The unit-state snapshot lost all six frozen Hard development games, with no
failures and unchanged checkpoint bytes. The representation/encoding capability
is verified, but no learned strength improvement is established by this run.
The next declared experiment combines the validated unit observations with the
finite-win objective and compares equal40-game training continuations from the
same immutable finite Easy40 model. Neither candidate changes the main default
or establishes acceptance. See the finite-spatial-continuation plan.

The unit-state curriculum exposed observed enemies in all 40 games, covering 94
protocol unit/structure identities, including different flying/ground combat
units, production/tech structures, detectors and workers. The largest sparse
unit-state record had 201 nonzero fields. The observations included both current
visibility and previously scouted snapshots; they do not reveal hidden totals.
Exposure receipt: `logs/audit/unit-state-exposure.json`.

The combined finite/spatial continuation source passes 72 tests. Its migration
appends the exact previously validated encoder to the immutable finite Easy40
model, preserving all old parameters/moments/RNG/reward/settings/horizon. The
resulting schema has 5,460 features. Independent review confirmed 1,000 snapshot
old-prefix/capacity-potential parity, sparse JSON reconstruction and all migration
arrays/hashes. The first real four-game training smoke completed without failures,
all 120-second cutoffs. Resume/frozen verification is next, separate from the
untouched input checkpoint. Artifact roots: `logs/ppo-finite-spatial/`,
`logs/ppo-finite-spatial-smoke/`, `logs/audit/ppo-finite-spatial-source/`.

Combined train4/resume2/frozen2 smoke verification completed without failures;
all eight were 120-second cutoffs and frozen checkpoint bytes are unchanged.
The equal-training 40-game control/candidate continuations are now running from
untouched finite Easy40 bytes and the matching migration. Results are pending.
Sources and initial checkpoints remain retained independently of smoke models.

The equal training continuation finished 40 additional Easy games per branch: the
finite control won 3, lost 19 and cut off 18; the richer-observation branch won 6,
lost 19 and cut off 15. Neither had failures. All opponent schedules match, and
initial 8 games have identical old observations/actions/times/outcomes/durations
and policy seeds across 8,183 decisions. Later RNG can diverge with rollout length.
This is modest training evidence, not frozen Hard acceptance. Both immutable
Easy80 snapshots now run matching Hard6 cases. Receipts:
`logs/audit/ppo-finite-spatial-first-batch.json`,
`logs/audit/ppo-finite-spatial-pairing.json`, and the continuation directories.

A separate exact-state counterfactual found that allowing the current stance
changes many frozen choices from switching to retaining it, but can also replace
unit production choices. It does not simulate the resulting new trajectories or
establish wins. The idempotent-stance archive now passes 71 tests, including two
red-to-green checks: both stances are legal with an army, and repeated selections
preserve the timer/pending orders. Actual switches still request orders. It adds
no attack schedule or hold period. A separate frozen six-game probe uses identical
finite Easy40 policy bytes, changing only stance-mask/command semantics.
Artifacts: `logs/audit/stance-mask-counterfactual.json`,
`logs/audit/ppo-idempotent-stance-source/`, `logs/ppo-idempotent-stance-hard6/`.

All three frozen Hard6 probes finished with six losses, no failures and unchanged
checkpoint bytes: finite-control Easy80, finite/spatial Easy80 and idempotent
stance with the original finite Easy40 weights. The modest Easy training gain
did not establish transfer to Hard. None is promoted as stronger than the
retained finite Easy40 snapshot. The stance counterfactual did not predict wins.
The next experiment should train directly on Hard and compare controlled
exploration, preserving richer live observations and the original acceptance scope.
