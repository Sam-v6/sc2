# Full-game SC2 imitation bootstrap, curriculum and league training

## What does the literature support about bootstrapping a capable policy?

### Takeaway
The strongest practical next direction is reuse of successful **training** experience, with live verification that the resulting stochastic policy can actually execute competent games. Copying AlphaStar's architecture or adding another hand-shaped reward is less justified. This recommendation is an inference for this repository, not an established SC2 CPU-only result.

### Cited Findings
- AlphaStar's January 2019 system started with supervised learning from human games; its initial agent reportedly won 95% against Elite. The subsequent league used many thousands of SC2 instances, 16 TPUs per agent and 14 days of training. These figures describe the preliminary January system, not the later Nature system. — [Official DeepMind account](https://deepmind.google/blog/alphastar-mastering-the-real-time-strategy-game-starcraft-ii/)
- The final AlphaStar league also started from supervised agents and reached Grandmaster with all three races. This is evidence for competent imitation initialization plus RL, not for starting a near-uniform policy on Hard. — [Official final-system account](https://deepmind.google/blog/alphastar-grandmaster-level-in-starcraft-ii-using-multi-agent-reinforcement-learning/)
- The official AlphaStar repository provides architectures, data readers and offline learning including behavior cloning. It explicitly does **not** provide online RL training code. — [Official code README](https://github.com/google-deepmind/alphastar)
- Self-Imitation Learning (SIL) stores state/action/discounted-return triples and applies a separate off-policy loss, with policy term `-log pi(a|s) * max(R - V(s), 0)` and a positive-residual value loss. The policy weight is treated as a target, not differentiated through the critic. The paper evaluates Atari and MuJoCo, not SC2; excessive imitation can limit later improvement. — [SIL paper, equations 1–3 and limitations](https://proceedings.mlr.press/v80/oh18b/oh18b.pdf); [author implementation](https://github.com/junhyukoh/self-imitation-learning/blob/master/README.md)
- AlphaStar Unplugged uses behavior cloning as the foundation for offline RL. It reports that top-quality filtering alone reduces dataset diversity/generalization; broader cloning followed by quality-filtered fine-tuning worked better. Return-conditioned cloning did not improve its results. — [Primary paper, sections 4.3 and 5](https://arxiv.org/html/2308.03526)

### Inferences
- **Prioritize archived self-generated data here.** Existing training trajectories already match the observation schema, legal masks, cadence and executor. Human replay adaptation would require a mapping from player commands into these 27 macro actions; scripted teachers introduce strategic knowledge that must not be hidden behind the phrase “learned macro.” Neither teacher source is needed for the first experiment.
- **Separate two algorithms honestly:** winning-episode masked behavior cloning is a supervised bootstrap; SIL is reward/value-weighted off-policy RL. Do not call a wins-only cross-entropy pass “SIL,” and do not feed old demonstrations into the PPO ratio objective as fresh on-policy samples.
- A bootstrap can preserve successful whole trajectories, unlike the earlier nine-state paired head fits. However, winning trajectories contain mistakes and luck; success filtering does not label every action as optimal. Weight games rather than letting long wait-heavy games dominate, retain all action classes without hand quotas, and split by whole game/case rather than by nearby frames.
- Sampling success matters: the repo repeatedly has useful greedy actors but poor sampled behavior. Offline accuracy or reduced entropy is not a success gate. Measure fresh sampled and greedy gameplay separately before authorizing a substantial continuation.

### Gaps
- No reviewed source establishes that SIL will beat varied Hard opponents with this specific tiny Terran policy on this CPU budget.
- The exact number and diversity of eligible successful training episodes still need an inventory. No evaluation game, discovery validation bank or reserved seed50000 trajectory should enter that inventory.
- The parent critic's calibration on old returns is not established by schema compatibility. A badly biased value baseline can make a purported SIL filter accept almost everything or nothing; report coverage by game, race, difficulty and action before learning.

## What transfers from curriculum and league methods, and what does not fit this budget?

### Takeaway
Adopt difficulty progression and retention of prior competence before attempting a distributed league. Published “small-scale” full-game systems often still use multiple GPUs, many simultaneous games and constrained matchups; their headline win rates do not directly establish feasibility for unrestricted Terran macro on this machine.

### Cited Findings
- Liu et al. use easier-to-harder opponent transfer and hierarchical control; their setting includes 4 GPUs, 48 CPU threads and 50 concurrent environments. Their tested Protoss-versus-Terran setup restricts military units. Mini-AlphaStar in the same comparison reaches zero level-7 wins after three days, while the hierarchical system performs much better. The paper also shows that high supervised action accuracy can accompany worse live play. — [JAIR paper, sections 3.5, 4.1, 5.2, 5.6](https://arxiv.org/html/2209.11553)
- Mini-AlphaStar's author code documents replay conversion, supervised training, live supervised-model evaluation, then RL. Its “single common machine” claim should not be read as a demonstrated CPU-only strong agent. — [Author repository](https://github.com/liuruoze/mini-AlphaStar)
- TStarBot-X uses 144 GPUs and 13,440 CPU cores and reports 25.7 million matches over 57 days. It uses imitation initialization, league diversity, historical-policy KL stabilization, and explicit expert-rule guidance. Its rule-guidance table includes strategic technology reactions; importing these would conflict with this project's no-hidden-macro-recipe constraint. — [Primary TStarBot-X report, sections 4.6–4.7, 5.1–5.2](https://arxiv.org/html/2011.13729)
- TStarBot1 and TStarBot2 must not be conflated: the former uses RL over a flat macro-action interface; the latter uses hand-coded hierarchical rules. Reported full-game results are Zerg-versus-Zerg on AbyssalReef. — [Original TStarBots paper](https://arxiv.org/abs/1809.07193)

### Inferences
- Difficulty progression should keep the **full-game win objective** and increase opponent strength, while retaining a fixed proportion of already mastered opponents. The failed collection-only transfer is not evidence that this form of curriculum fails: it changed the objective and learned an economy-only policy.
- A small fixed opponent panel across races/builds/maps is the affordable analogue of diversity, not a claim to implement AlphaStar's league. Add a few historical learned opponents only after reliable built-in wins; a full exploiter population is premature and doubles important simulator/inference work.
- Promotion should be based on frozen performance by race and difficulty, with uncertainty and independent cases. Harder/VeryHard/Elite progression should follow demonstrated competence rather than moving every fixed 40 games. Preserve easy-case checks to detect forgetting. Cheating built-ins are a separate target because their advantages change the problem.
- These papers cannot justify “32–64 unsuccessful games proves convergence failure.” Conversely, scaling a repeatedly collapsing policy without a viable sampled-behavior check wastes simulations. First demonstrate that the data collection policy can sustain successful full games; then give a declared promising method a meaningful fixed training budget rather than repeatedly changing several ingredients.

### Gaps
- No credible estimate of CPU-only time-to-Elite follows from these papers. Avoid wall-time promises or describing a commercial-server/GPU result as laptop-scale.
- The relevant methods bundle architecture, data, action abstraction and training scale. Their wins are not controlled evidence that one knob—GAE, entropy, replay, or hierarchy—alone will fix this repository.

## Which one or two implementations should this repository prioritize?

### Takeaway
First build a training-only successful-trajectory bootstrap with explicit replay retention; second, if sampled competence survives, run a full-game difficulty curriculum with retention checks. Defer human/scripted teachers, large leagues, and the unfinished saving-option probe until this more directly literature-supported data-reuse path is tested.

### Cited Findings
- The local economic arm improved collection but produced zero army in all 12 Hard transfer games; the combined reward continuation also failed its declared Hard gate. Therefore repeating a collection reward is not the proposed intervention. — [Local experiment ledger](/home/sam/repos/sc2-repos/sc2-void-bot/.worktrees/terran-rl/docs/experiment-results.md)
- The five-second unit-intent arm was implemented and failed; it must not be rediscovered as untried. — [Local intent experiment and closure](/home/sam/repos/sc2-repos/sc2-void-bot/.worktrees/terran-rl/docs/superpowers/plans/2026-10-04-unit-intent-experiment.md)
- Replaying positive-return experience has a published off-policy objective, whereas the official SC2 offline-learning work makes imitation initialization explicit. — [SIL](https://proceedings.mlr.press/v80/oh18b.html); [AlphaStar Unplugged](https://arxiv.org/abs/2308.03526)

### Inferences
**Priority 1 — a bounded bootstrap/data-reuse experiment, not another head-fit search.**

1. Make an immutable manifest of complete, compatible combat **training** episodes: exact encoder/actions/executor/cadence, fog-respecting snapshots and legal selected actions. Exclude debug fixtures, economic-only objectives, all evaluation modes, and validation/discovery-validation cases. If multiple reward versions exist, either select one version or explicitly reconstruct one common combat objective from recorded components; never compare incompatible returns silently.
2. Split by entire case/game. Preserve the original parent. Train one masked whole-actor behavior-cloning candidate on successful training episodes with a predeclared small CPU budget, e.g. at most five passes, one thread, bounded minibatches. This is a recommended pilot design, not a paper-prescribed hyperparameter. The body is trainable; this is not another tiny-label frozen-head correction. A game-level training holdout limits overfitting, but determines no gameplay-strength claim.
3. Run one fresh paired gameplay screen including **sampled** execution at the policy's actual training distribution and greedy execution. A concrete allocation is 12 cases across races/maps, parent and clone in both modes: 48 games maximum, existing concurrency cap. Predeclare a sampled-win improvement requirement and a greedy nonregression requirement. If cloning only improves offline accuracy, stop. Do not temperature-sweep the screen until it passes.
4. Only a viable candidate proceeds to a separately declared continuation that retains successful experience through a separate SIL-style off-policy loss, alongside ordinary on-policy combat learning. Keep the original kill/victory objective. Do not center the positive SIL weights into negative values; stop-gradient the weights. Use fresh optimizer state after BC and handle value calibration explicitly. Start with one fixed replay schedule, not a tournament over replay rates.

This route still has failure modes: a small success set may reproduce a narrow rush; near-identical states with incompatible good continuations may need memory/context; distribution shift can break BC; SIL can reinforce lucky returns or inhibit improvement. Those are reasons for whole-game splits and fresh live checks, not reasons to train on protected evaluations. It remains genuine learned macro because neither the teacher nor the executor supplies a handwritten build order.

**Priority 2 — competency-based opponent curriculum after bootstrap viability.**

Use the full combat task throughout. Predeclare a fixed mix of current-frontier and mastered opponent cases, frozen race/build/map panels, a maximum episode budget, and evaluation intervals. Move upward only when the frozen policy meets a stated per-race reliability criterion; keep historical lower-level tests and successful replay to detect forgetting. This is deliberately smaller than a league and requires no new network inputs. A useful initial experiment would be a single two-difficulty transition with a fixed budget, not a promise to climb all difficulties in one run.

**Human/scripted-teacher comparison:** Human demonstrations may offer strategies absent from self-play archives, but raw replay conversion, player-perspective filtering and action mapping are additional engineering risks. A scripted teacher can generate correctly mapped examples cheaply, yet its strategy is a human-designed bootstrap; it must be disclosed and separately authorized if the user rejects scripted macro knowledge. Self-generated successful training episodes are therefore the cleanest immediate source. None of these methods proves that the resulting policy exceeds its teacher until fresh RL gameplay demonstrates it.

### Gaps
- This research turn does not authorize fitting or games. Exact data volume, training holdout composition, optimizer budget and gameplay effort gates must be frozen in the implementation plan.
- The suggested CPU schedules are bounded experimental choices, not published optimal settings. No primary source establishes an optimal replay coefficient or curriculum promotion threshold for this repo.
- Better sampled performance may come from imitation alone; label it as bootstrap progress. Improvement beyond that policy requires subsequent reward-driven learning and independent evaluation.
