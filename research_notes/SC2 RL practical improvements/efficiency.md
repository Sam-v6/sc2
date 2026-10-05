# Practical sample efficiency for full-game SC2 RL

## Which full-game results transfer to our compute and goals?

### Takeaway

Full-game literature supports action abstraction, hierarchy, curriculum and learning from demonstrations, but its successful experiments still use substantial compute or constrained scenarios. We should reuse these mechanisms selectively, preserving learned macro decisions, rather than expect a wholesale algorithm replacement to produce immediate all-race ladder strength.

### Cited Findings

- HierNet uses extracted action sequences and hierarchical policies trained with PPO, reporting 93% against level 7 and 96/97/94% against cheating levels 8/9/10. Its stated machine has four GPUs and 48 CPU threads. The authors acknowledge small maps and only the first two combat unit types; this is not unrestricted Terran ladder evidence. The later cheating-level setup uses win/loss reward and training from scratch. Section 6.4 reports benefits from more episodes per update, larger minibatches, more epochs and shared policy/value layers. Appendix D sets gamma=1, lambda=1, clip=.1, value coefficient=.01, entropy coefficient=1e-5, learning rate=1e-4, batch64 and20epochs. These are coupled settings, not universal defaults. — [HierNet paper](https://arxiv.org/html/2209.11553v1), [author repository](https://github.com/liuruoze/HierNet-SC2).
- SCC is directly relevant to Terran: it first learns from human replays, then applies PPO with entropy and a KL penalty to the supervised reference. It reports strong supervised performance using 4,638 replays, with the best supervised setup also using a much larger dataset. RL experiments are Terran versus Terran on Triton. Separate critics serve win/loss and human-strategy rewards. An initial policy-frozen value warm-up addresses noisy advantages. None of this establishes that a few dozen CPU-only games can reproduce its strength. — [SCC paper, sections5–6](https://proceedings.mlr.press/v139/wang21v/wang21v.pdf).
- SMAC is a cooperative multi-agent **micromanagement** benchmark; its results do not demonstrate full-game economic, production, scouting or technology learning. — [SMAC paper](https://arxiv.org/abs/1902.04043).

### Inferences

- Our current main agent already has atomic production commands, scripted worker/combat execution, masks and PPO; these overlap important abstractions in published successes. Literature should help identify missing temporal abstraction or data reuse rather than motivate copying an entire framework.
- Our future Hard→VeryHard→Elite progression needs evaluations against varied races/builds/maps. Cheating difficulties and multiplayer are separate generalization targets. Published restricted-map win rates should not be presented as expected performance here.
- A hierarchy could separate economy, production, scouting and combat decisions, without hard-coding a build order. However, simply copying the paper's unit caps or expert desired unit counts would conflict with the user's open-ended macro intent.
- The ongoing saving-option diagnostic tests one possible action-interface limitation. It is not a literature-established cure, and the prior five-second unit-intent arm already failed locally. Research does not justify quietly extending that failed arm.

### Gaps

- I found no primary result guaranteeing robust all-race full-game Terran learning under this project's four-engine, CPU-only operating envelope.
- The small-compute papers are materially different interfaces and scenarios. We cannot infer their learning curves or win rates for our observation/action schema.

## Can self-imitation reuse successful training without cloning validation labels?

### Takeaway

Self-Imitation Learning (SIL) is a concrete, small implementation opportunity: supplement on-policy PPO with a distinct positive-advantage replay objective using the agent's genuine completed **training** trajectories. Its empirical support is outside full SC2, so the next step should establish feasibility and gradients before any claim of improved play.

### Cited Findings

- SIL stores `(state, action, discounted episodic return)`, then minimizes `L_actor=-log pi(a|s)*(R-V(s))_+` and `L_value=.5*((R-V(s))_+)^2`. A state/action contributes only when its past return exceeds the current critic estimate. The paper interleaves ordinary actor-critic and SIL updates, prioritizes replay by positive advantage, and explicitly distinguishes SIL from importance-corrected off-policy policy evaluation: SIL itself has no behavior-policy importance ratio. It reports A2C improvements on Atari and PPO improvements on some MuJoCo tasks; there is no full-SC2 experiment. Section5.6 says the PPO combination lacks the strong theoretical connection given for A2C. — [SIL primary paper, equations1–3 and algorithm1](https://proceedings.mlr.press/v80/oh18b/oh18b.pdf).
- The author's implementation stops the actor advantage gradient, clips advantage to[0,1], uses prioritized replay, replay-sampling importance weights, and normalizes by `max(number_of_positive_samples,64)`. Its code defaults include replay alpha=.6 and beta=1. Replay importance weights correct biased buffer sampling, a different issue from behavior-policy importance ratios. The buffer retains episodes with any positive reward, not only victories. — [Author source, lines168–176,246–254,286–311](https://raw.githubusercontent.com/junhyukoh/self-imitation-learning/master/baselines/common/self_imitation.py).
- PPO's original method alternates fresh policy data collection with several optimization epochs on that data. Its clipped policy ratio is not a blanket justification for indefinitely reusing arbitrary historical actions/advantages. — [PPO primary paper](https://arxiv.org/pdf/1707.06347).

### Inferences

- A minimal CPU Torch experiment can implement the plain SIL equations with **uniform sampling** over all eligible completed training episodes. This is a declared simplification of the paper's prioritized replay, reducing moving parts for the initial audit. Use a plain mean objective; do not silently combine positive-only normalization and prioritization. Report positive fraction so tiny actor signal is visible.
- Do not center SIL weights across the batch. Centering creates negative weights, defeating the defining positive-part objective. Compute `positive=(return-current_value).clamp(min=0)` and detach it in actor loss; value loss differentiates through the critic. Original actual legal masks must constrain categorical probabilities.
- A win-only dataset would amplify every action in successful trajectories, including useless worker spam or waits. SIL's state-level return filter is more selective, but still cannot prove that the credited action caused success; historical lucky outcomes and reward hacking remain risks.
- Both reward and value must share the original reward version, scaling, gamma, macro cadence, feature and action schema. Do not reuse collection-only/composite-reward returns or critics, and do not replay old stored **advantages** as current SIL weights.
- Sampling all outcomes lets good fragments of losses contribute and avoids winner-only behavior cloning. Race/map/build coverage and action-weight mass should be disclosed; Easy victories may teach behavior that remains weak against Hard.
- Separate actor/body and critic/body gradient measurements are important because the existing network shares a trunk. Detaching the actor weight prevents accidental actor gradients through the critic, but it does not prevent the explicit SIL value loss from moving the trunk. Freezing the trunk would create a different head-only variant; do not call that the original SIL approach.
- Optional KL anchoring to the retained parent is inspired by SCC's reference-policy regularization, but remains a local addition. It should not select among dozens of offline fits based on Hard evaluation labels.

### Gaps

- Whether the retained critic produces enough positive advantages on valid old training experience is unknown until measured. Overestimated values could suppress SIL entirely.
- Positive replay loss reduction and preserved anchor KL cannot establish stronger gameplay. Fresh frozen games and fresh on-policy training are required.

## What is the smallest useful next experiment in this repository?

### Takeaway

Run a zero-game data/gradient audit for same-context SIL before building a new learner or hierarchy. If it passes, compare a fixed PPO+SIL schedule against ordinary PPO using equal fresh training cases and independent frozen gameplay evaluation.

### Cited Findings

- Locally inspected `ActorCritic` has a 64-unit shared tanh trunk, masked categorical actor, scalar critic, lambda1 completed-episode returns, and four PPO epochs. The helper normalizes PPO advantages, trains actor/value/entropy jointly, clears rollout after the update, and has no self-imitation buffer/loss. — [actor_critic.py](/home/sam/repos/sc2-repos/sc2-void-bot/.worktrees/terran-rl/src/rl/actor_critic.py), [ppo_update.py](/home/sam/repos/sc2-repos/sc2-void-bot/.worktrees/terran-rl/src/rl/ppo_update.py).
- A fresh read-only receipt scan found40 training games with8 victories in `logs/ppo-combat-kills/easy-1`, and40 with18 victories in `easy-2`. All scanned game receipts identify `mode=train`, `reward_version=combat-kills-v1`, nominalmacro1 anddifficultyEasy. Per-batch behavior checkpoints and action logs remain; per-episode candidate availability must not be assumed. — [easy-1 training evidence directory](/home/sam/repos/sc2-repos/sc2-void-bot/.worktrees/terran-rl/logs/ppo-combat-kills/easy-1), [easy-2 training evidence directory](/home/sam/repos/sc2-repos/sc2-void-bot/.worktrees/terran-rl/logs/ppo-combat-kills/easy-2).
- The current transition code attaches each action's next-step reward to that same decision row and finalizes the final action on game end. Current combat shaping is scaled terminal payoff plus potential difference plus enemy-value killed delta. This permits discounted returns from complete reward rows, subject to confirming historical relevant semantics. — [terran.py transition/end callbacks](/home/sam/repos/sc2-repos/sc2-void-bot/.worktrees/terran-rl/src/rl/terran.py:312).
- Existing local independent-value, larger-batch, lower-learning-rate, sensory and combined-reward arms fail declared gameplay gates. The prior joint head fit used nine counterfactual paired states with fixed body/critic; full-trajectory positive-advantage replay would be a materially different intervention. — [experiment-results.md](/home/sam/repos/sc2-repos/sc2-void-bot/.worktrees/terran-rl/docs/experiment-results.md), [prior head-fit protocol](/home/sam/repos/sc2-repos/sc2-void-bot/.worktrees/terran-rl/docs/superpowers/plans/2026-10-05-joint-minimum-change-head.md).
- IMPALA corrects actor/learner policy lag using V-trace and demonstrates throughput/data benefits on Atari/DMLab. It is a more involved algorithm change; those benchmarks do not prove our full-game SC2 benefit. — [IMPALA primary paper](https://arxiv.org/abs/1802.01561).

### Inferences

Proposed sequence, with no new game or model mutation in this research task:

1. Create a new isolated experimental loader/loss module. Freeze exact input receipts, behavior checkpoints and action ledgers. Require mode=train, completed native result, intact matching replay, matching schema/reward/gamma/scale/cadence, valid actual mask/action, finite rewards and complete row count. Reject evaluation/development traces from fitting, particularly all reserved final cases. Preserve existing frozen artifacts.
2. Reconstruct states with the compatible encoder and returns backwards from per-action rewards, zero terminal continuation. Independently compare behavior probabilities/action RNG where feasible and reward arithmetic/terminal payoff. Existing hashes alone do not prove historical/current semantic equivalence: inspect relevant frozen source/checkpoints. If context differs, exclude that dataset without adapting its labels.
3. Test scalar numerical gradients and actual masks. Cases: negative advantage gives zero SIL update; actor weight is detached; illegal actions have zero probability; critic below return gets upward value gradient; empty-positive batch yields finite zero signal. Demonstrate original PPO path unchanged.
4. Without an optimizer step, measure positive-state count/fraction, per-race/action weighted mass, complete-return/current-value distributions, actor and critic/body gradient norms/cosines, and comparable PPO signal on valid completed training data. Report weighted late-game versus early-game mass and wait/SCV/army fractions. No hand-selected recipe target.
5. Freeze one bounded schedule and coefficient from training-only scale diagnostics, not an outcome sweep. Preserve a parent/control. Use fresh on-policy games for PPO; replay buffer receives only training trajectories. SIL updates occur separately, use current critic, and do not enter the PPO old-log-probability parity check. Record actual optimizer steps and buffer hash/context.
6. Evaluate immutable parent, ordinary PPO control and PPO+SIL on a newly frozen balanced bank. Report win/return gain, lost parent wins, collapse/army production and uncertainty. Stop on the declared bound; do not search forever for a favorable bank. Strong Hard evidence is an intermediate gate before progressing to VeryHard/Elite and eventual multiplayer.

### Gaps

- These notes propose a test; they do not implement SIL or promise a strength gain.
- No new training, optimizer steps, SC2 games, package installs or model-file writes were performed for this literature review. Only this research note was written.
