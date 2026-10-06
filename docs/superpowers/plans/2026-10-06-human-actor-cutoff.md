# Human imitation: learn the actor selection cutoff

Goal: improve autonomous exact unit groups after the three-player audit found that human-size top-K ranking recovers 3545/4189 groups, versus 2238 with the current cutoff. This is a diagnosis using human answers, not an autonomous result.

Scope: add one zero-initialized 32-weight shared logit bias conditioned on the same context/ability used for actor ranking. Keep arbitrary group sizes, eligible-unit masks, fallback selection, all command heads and losses. Keep legacy checkpoints and the default model unchanged. No RL/native games, reserved replay predictions, downloads or GPU.

- [x] Observe failing tests for missing cutoff support; implement opt-in inference, analytic gradient, checkpoint metadata and trainer flag.
- [x] Verify scene-dependent group selection, uncapped groups, numerical cutoff/shared gradients with ranking enabled, initial legacy equivalence and checkpoint round trip. Full suite: 230 tests, plus Ruff/diff checks.
- [ ] Freeze the same eleven teaching games / Rom diagnostic split, fresh seeds 7000/7001, refinement enabled, hidden32, batch16, rate0.001, 169 epochs /44278 updates /707941 presentations. Only the cutoff is added, initialized zero, so existing weights start identically.
- [ ] Run CPU-only two-thread fit with 900-second fit /1050-second caller limits. Follow the live handle; bound production files stay unchanged during fitting.
- [ ] Reload baseline fit03 and candidate on identical cohorts, check source/checkpoint/code bindings, per-player full commands and actor size/ranking errors. Frozen 95% ability /90% groups /75% complete teaching gate; no acceptance or native/RL if it fails. Coarse spatial errors remain a separate issue.

The previous goal turn made progress: terminal diverse fit and common-cohort comparison, actor-size oracle diagnostic, evidence recorded in commit d0041a9. The whole professional imitation/micro/full-game/Hard/higher-difficulty roadmap remains open.
