# Direct critic-feature gradient experiment

The stronger victory-credit continuation scored 3/40 training wins but regressed
to 0/30 frozen Hard wins. The best retained policy stays kills-only Easy40 at
12/30. A conditional gradient diagnostic on the control's first winning batch
found weighted critic body gradients substantially larger than policy body
gradients. That does not establish the cause of the losses.

## Contract and one-factor protocol

1. Copy the victory-credit source and untouched initial weights. Change only
   the critic's direct backpropagation into shared actor features: its value
   head reads `hidden.detach()`, while actor gradients still train the feature
   body. Declare `settings.critic_feature_grad=false` in strict checkpoint
   context. Rewards, observations, macro/micro, inference, optimizer settings,
   discount, λ=1, initial arrays/RNG/counters and moments stay unchanged.
2. Verify real Torch value-only supervision with a sole legal action and zero
   initial moments. The critic must fit returns while actor parameters/logits
   stay exact. Verify existing contextual policy learning and Adam resume, and
   reject the prior shared-gradient context. Record explicit metadata migration.
3. Complete isolated train/resume/frozen checks on separate smoke copies. Then
   run a bounded Hard40 continuation from untouched initial using the retained
   victory-credit control schedule: seed base 30000, both maps, all races and
   five builds, 1200 game seconds/300 wall seconds, four workers, cadence one.
4. Freeze the final and evaluate matching greedy Hard30 development cases,
   seed 20000. Audit terminal outcomes, reward components, full returns, context,
   numerical payloads and frozen hashes. Preserve controls and the 12/30 parent;
   acceptance still needs the unchanged Hard target and fresh seed bank.

This blocks only direct value gradients into actor features. Inherited Adam
moments can still move the body, and global clipping couples critic-head norms
to actor updates. Nothing is reset. A critic with policy-only features may fit
less well and increase advantage variance. These are experimental risks.

## Verification

The two new tests failed before implementation. The corrected isolated source
passes 82 tests, including real Torch value fitting without actor changes and
existing contextual policy-learning/resume tests. Independent review confirmed
this contract, exact migration and strict context rejection; it found no material
defect. Source: `logs/audit/ppo-critic-isolation-source`.

Only `settings.critic_feature_grad=false` changes in migrated metadata. Every
numeric array and all other metadata are exact. Parent is the untouched
victory-credit initial, not its failed trained final. Receipt:
`logs/ppo-critic-isolation/migration.json`. Immutable initial SHA-256:
acc3e72f09c98ba12974419c9db9803bdf8cb83f6f5947bd5dd90a626337273f.

Separate two-game train/resume/frozen checks completed with zero failures
(all six games reached their 120-second horizons). Resume chained hashes,
retained cadence one and the declared graph context, and advanced the optimizer
676->684 updates. All numerical payloads were finite; experiment initial and
canonical inputs remained untouched. Receipt:
`logs/audit/critic-isolation-smoke-results.json`.

The untouched initial is now running the bounded Hard40 continuation. Main
production code and the strongest retained model remain unchanged.
