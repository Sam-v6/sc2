# Episode Coherent Exploration Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline under existing autonomous authorization.

**Goal:** Test whether small, whole-episode policy perturbations preserve viable Hard trajectories while producing genuinely different macro behavior.

**Architecture:** A frozen diagnostic uses the retained policy, original one-second cadence,5460live features,27actions and unchanged executor/reward. Four fixed zero-mean output-bias directions and their antithetic negatives are held constant throughout each game; action selection is masked argmax. This is exploration verification, not a PPO training run or strength acceptance.

**Tech Stack:** Existing NumPy, BurnySC2, supervised headless runtime; no new dependencies.

**Spec:** The conditional Astra advisory recorded in docs/superpowers/plans/2026-10-04-unit-intent-experiment.md. Advisory hypotheses remain unproven.

## Global Constraints

- Parent checkpoint0f3e05d9efd5eba4fd238a6282e462599ffc675f008b98fd42925e99f6bb16c6, original gamma/cadence/observations/actions/micro/objective intact.
- No scripted macro sequence, unit mix, research or attack timing. Only learned policy output biases are perturbed, once per episode.
- Direction RNG71331: four27-dimensional standard-normal vectors, subtract each mean and normalize each RMS to1; include their exact negatives. No reward-based direction selection.
- Calibrate one shared scale to approximately5%changed greedy decisions across retained recorded60-game33556-state masks, without filtering outcomes. Record all eight rates and require mean within0.5percentage points of5%; otherwise stop before games.
- Training-case RNG71332 chooses two different races and two random builds, one map each; fresh seeds80000/80001. Exact outcome-uninspected cases:80000ZergPowerSimple64;80001ProtossRushTritonLE. Existing receipt search finds neither seed. Do not replace cases based on results.
- At most18games: two original-policy controls first; if both lose/tie, stop inconclusive without running the16perturbed-policy games. Otherwise run all eight policies on both fixed cases. This ordering saves unnecessary games and does not select cases or directions using outcomes.
- Actual games use ordinary resources, tech, fog and supply. No debug cheats.1200game seconds/180wall seconds. Quiet wrapper: eight CPUs,nice+10,BLAS1,CPU-only,<=4games total.
- Finish the current matched intent/control comparisons before launching this pilot. Acceptance50000 remains reserved; used development banks are not final proof.
- Preserve all frozen inputs, source/code hashes, replay/JSONL/receipts, all failures. Refuse overwrite. An infrastructure failure is not learning failure; preserve it and require a full, explicitly recorded repeat rather than selective replacement.
- Deterministic pilot trajectories never enter the categorical PPO updater. Any later parameter-space policy-search learner must be separately labeled and tested.

## Review Focus

- Perturbed and original forward passes differ only by the declared output-bias vector; value head, optimizer arrays and other parameters/RNG remain exact.
- Calibration state/action schemas and parent greedy choices reproduce immutable old checkpoints; directions/scales do not use rewards.
- Each policy keeps its perturbation for the entire episode; no action-by-action random exploration.
- All cases and once-only game receipts completed without exceeding four workers; wall timeout/cancellation retain owned-group cleanup.
- Actual visited-state deviations are verified against parent masked argmax; recorded winning perturbations must change executed macro behavior rather than only noop waits.

### Task 1: Frozen calibration and inputs

- [x] Create logs/audit/episode-bias-calibrate.py and logs/episode-bias-exploration input manifest.
- [x] Verify all33556original greedy choices, zero-mean/antithetic directions, shared scale/rates, exact unchanged parameter groups and closed-form logits; parent/inputs immutable.
- [x] Save eight frozen diagnostic policy files plus byte-identical parent and exact two-case metadata, source hashes and explicit no-training label. No source/model writes in sibling folders.

### Task 2: Supervised ordinary-game pilot

- [x] Reuse src.runtime.supervise and frozen episode execution, four or fewer games, with cancellation/timeout cleanup; verify the batch limit and incomplete/failure receipts before actual jobs.
- [x] Run original controls first. If neither is Victory, record inconclusive preservation and stop; no quiet scale/case enlargement.
- [ ] If a control wins, run all16predeclared perturbation/case games from unchanged weights and produce genuine replays/action logs.

### Task 3: Behavior and outcome audit

- [x] Reconstruct parent and perturbed greedy choices on each actual visited state; record discounted return, unit production, supply-zero time, stance changes, completed outcome, and checkpoint/source immutability.
- [ ] Progress requires at least two different perturbation IDs winning a case won by its parent control, each with>=5changed executed non-wait macro decisions and>=1%changed decisions among non-forced choices; paired discounted returns must vary by>1e-8. New wins on parent-losing cases are reported separately, not substituted for the preservation criterion.
- [ ] If policies reproduce parent behavior or destroy every parent victory, stop this local bias route. If progress passes, define one small antithetic-return parameter-search RL arm; the diagnostic alone neither proves learning nor Hard generalization.
- [ ] Existing frozen14/13development effort gate and final70%30-game acceptance remain unchanged. Do not promote a winning training-case perturbation.

## Calibration ledger

Outcome-free calibration reconstructs all33556 parent greedy choices. Shared scale0.03118564886972308 yields mean5.0002235percent changes, individual2.97115–9.78067percent. Four RNG71331 directions and negatives, all unchanged parameter/moment arrays and metadata, zero rollout, copied source and checkpoint hashes independently reviewed. Receipt `logs/episode-bias-exploration/inputs.json`. Cases are hardcoded predeclared values in the manifest; separate reproduction of default_rng71332.choice(races,size=2,replace=False) then choice(builds,size=2) produces Zerg/Protoss and Power/Rush. Controller batch-bound/failure self-test passes; two controls launched only after all prior games terminate.

## Final diagnostic closure

Both original controls complete with ordinary Defeat, zero failures:80000ZergPowerSimple64,510decisions/231executed non-wait macros/discounted return-.06456936;80001ProtossRushTritonLE,543decisions/178executed non-wait macros/return-.05780200. Audit reconstructs all1053masked greedy choices, both exact cases, replays, source/controller/inputs/checkpoint hashes, unchanged update counters and absent training candidates. Status inconclusive_no_control_victory. Per declaration, no16perturbation games, no promotion and no extra cases. The remaining conditional perturbation/progress tasks are intentionally unexecuted; this does not refute episode-coherent exploration. Receipt `logs/episode-bias-exploration/audit.json`.

The resource sampler overlapped process termination, so its0.44–2.44percent hostCPU/10percentGPU22W reading is primarily post-game, not a live-game peak guarantee. A sampled owned process still used affinity24–31/nice10. Prior actual four-game measurements remain13.04–13.52percent CPU.

Independent controller review identified an interruption receipt-retention gap: cancelled workers were joined, but a KeyboardInterrupt skipped harvesting the active batch results. Neither completed control was interrupted. Preserve original controller/hash; `source/pilot_v2.py` fixes future execution by harvesting after cancellation/join and writing every result before stopping. Mock interruption regression plus4worker peak/failure/0-and5batch rejection tests pass. Frozen source/actual receipts remain unchanged.

The first correction also lost already-submitted futures if interruption occurred during the submission comprehension. The unexecuted v2 controller now appends futures incrementally; regression interrupts the second submission and verifies the first job's retained cancellation result. Waiting-interruption and submission-interruption tests both pass.
