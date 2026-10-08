# Combined Combat and Collection Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline. Steps use checkbox syntax; the user has already authorized autonomous execution without confirmation pauses.

**Goal:** Learn Terran macro with intermediate enemy destruction and harvesting feedback, then demonstrate improvement in ordinary Hard games.

**Architecture:** Retain the existing 5,460-feature, 27-action PPO actor and atomic executor. One reward objective combines the existing combat return with resource-collection increments; retain one critic and the existing optimizer implementation. Keep this experimental context separate from production checkpoints.

**Tech Stack:** Existing Python 3.12, NumPy, BurnySC2, sibling CPU Torch runtime and SC2 4.10/build 75689; no installations.

**Spec:** User's autonomous Terran RL goal and suggestion of intermediate unit/building kill rewards; [verified collection and transfer results](2026-10-05-resource-collection-learning-results.md).

## Global Constraints

- Work in the existing `Sam-v6/terran-rl` worktree. Preserve all older frozen source, manifests, receipts, models and sibling files.
- Maximum four engines, eight-CPU nice +10 wrapper, CPU-only updates, sampled 80% whole-machine ceiling and 50% baseline gate.
- No scripted build order, worker quota, army mix, attack timing, new observations or evaluation-data fitting.
- Per transition reward is exactly `.01 * (victory_bonus + gamma*next_potential - previous_potential + delta_enemy_value/100 + delta_collected_resources/1000)`.
- `victory_bonus=100` only on actual victory; potential and enemy value retain production semantics. Collected minerals and gas are monotonic authoritative score counters. Spending/refund/loss fields do not enter collection credit. Subtract initial counters once; no double payment at terminal callbacks.
- Distinct `combat-kills-collection-v1` reward version and `ppo-composite-reward` algorithm. Gamma `.9979919516614258`, lambda 1, scale `.01`, one-second macro cadence, all other PPO settings unchanged.
- Initialize from immutable `frozen-easy40.npz` SHA `0f3e05d9efd5eba4fd238a6282e462599ffc675f008b98fd42925e99f6bb16c6`; copy actor/body/RNG exactly, zero critic/all moments/global optimizer age together, clear rollouts and task counters. Record original 676 updates and 144 episodes/attempts separately.
- Train exactly 64 Medium games, 1,200 game / 180 wall seconds, seeds 114000–114063; races/builds/maps cycle 3/5/2 as before. Four complete validated trajectories per update, final checkpoint only, no restart/extension/model selection.
- Then exactly 12 paired greedy Hard cases, seeds 115000–115011, four per race, both maps/all five builds, ordinary combat scoring, 1,200 game / 180 wall seconds. Require at least two additional wins, nonlower mean ordinary discounted return and positive win gains in two races. Failures prevent complete-coverage claims; no case replacement.
- Only after a passing independent Hard development review may reserved 50000–50029 acceptance run: at least 21/30 wins, all races/builds/maps. Maximum 118 actual games: 64 training, 24 development, conditional 30 acceptance. Unused-case scan and manifest freeze precede every new live phase.

## Review Focus

- Cancellation/spending must not earn harvesting credit; validate counter increments and telescope from recorded observations.
- Terminal collection must be paid once, including natural defeat and horizon Tie; retain incremental decision/reward journals on interruptions.
- A combined reward checkpoint must not silently load as a production PPO resume; inference adapter restores ordinary scoring without changing actor choices.
- Every batch must share behavior weights/moments/age and reconstruct sampled choices, log probabilities and discounted MC returns before updating.
- Actual spawned workers must resolve unique module names even with older experiment directories present; every completed result must survive interrupted auditing.

## Design decision and limits

The reviewed zero-update 50/50 task-gradient diagnostic supports local coexistence, not this reward ratio, optimizer behavior or gameplay. Instead of adding two critics/task-conditioned inputs, test the simpler single combat objective with collection credit worth one tenth of enemy destroyed value in the same resource units. This changes the objective and resets its value/optimizer context explicitly. Positive harvesting reward can still favor excessive economy or longer losing games; the fixed ordinary-combat Hard evaluation must expose that. Do not change the ratio after seeing results.

### Task 1: Typed context and combined reward

Create ignored `logs/combined-combat-collection/source/combined_policy.py`, `combined_bot.py`, and `test_combined.py`. Reuse unchanged reviewed constants/journaling from the collection runtime. Implement `CombinedPolicy`, `migrate`, and inference-only `CombatEvaluation`; retain six network arrays. Implement incremental collection reward on top of the unchanged combat transition.

- [ ] Write failing tests for exact actor migration, zero moments/critic/age, context rejection, inference parity/forbidden saves and resource increment reward with repeat-terminal/cancel-like counter cases.
- [ ] Implement the minimal context and reward; run tests with the worktree Python under `tools/low_load.py`.

### Task 2: Real worker, optimizer and trajectory validation

Create `combined_worker.py`, `combined_validate.py` and `ppo_update.py` in the same source directory. Reuse the existing PPO helper with only its policy-class import changed. Workers journal ordinary games and retain complete rollouts/replays; validation reconstructs stochastic choices, combined rewards, gamma-discounted MC returns, critic advantages and likelihoods.

- [ ] Write failing real-spawn, reward-corruption, incomplete-trajectory and temporary CPU Torch update/resume tests.
- [ ] Implement worker/validator/helper; run the source suite and production suite. No actual disposable smoke games outside the budget.

### Task 3: Fixed controller and immutable live evidence

Create `combined_controller.py` and cancellation/batch tests. Reuse the reviewed CPU monitor; use unique combined module names. Freeze initial model, maps, source, this protocol, independent reviews, fixture accounting evidence and exact case banks before games.

- [ ] Test same-behavior merge, exact episode/attempt counters and interrupted receipt harvesting.
- [ ] Implement prepare/train, independently review the entire source/protocol, then freeze and run 64 games. Keep all behavior, learner-input/output/after snapshots and receipts. Independently audit all actual data before evaluation.

### Task 4: Ordinary Hard development and conditional acceptance

Create separately reviewed/frozen evaluation source after training completes. Validate actor choices and ordinary combat rewards independently. Record all regressions and failure cases; promote no candidate on auxiliary rewards alone.

- [ ] Run the 24 fixed paired development games and independent complete-data audit. Close this experiment if any declared development gate fails.
- [ ] On success only, freeze reserved acceptance cases and run/audit 30 games. Update README/results/replay evidence together; reliable Hard strength remains unproven until that gate passes.
