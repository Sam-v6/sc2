# Value-feature fit diagnostic

The declared-race arm failed its joint frozen-development gate. Do not extend
or promote it. Its actual collection-batch value predictions explain only
0.091–0.186 of return variance after updates, despite a value-head update on
each actor minibatch. The current `critic_feature_grad=False` path fits a
linear head on features changed only by actor training. This is a measured
fit limitation on training states, not a demonstrated explanation of losses.
Receipt: `logs/audit/declared-race-value-fit.json`.

Before implementing another gameplay arm, compare a fixed-feature value head
and a separate trainable value body on retained eight-worker near-greedy first
batch data. Both start with identical raw predictions from the untouched
near-greedy initial checkpoint. Keep the actor entirely unchanged. Use a cloned
64-unit tanh body for the independent value model, without introducing new
observations or macro actions. This is a diagnostic, not adopted architecture.

Use all decisions of the original first eight actual games. Hold out complete
games 30144 (Terran defeat) and30149 (Zerg victory); train on the other six,
including the Protoss victory. Record exact source/game hashes and discounted
finite Monte Carlo returns. Both fits use fresh critic Adam state, rate0.0003,
eps1e-5,256-state minibatches, maximum gradient norm0.5 and the same seeded
shuffle orders. Fresh optimizer state in both controls avoids claiming parity
with inherited production Adam. Evaluate at epochs0,4 and32 on both training
and held-out games; preserve initial and fitted arrays separately.

Record MSE, explained variance and prediction ranges per split and per game.
A separate value-body gameplay experiment is justified only if held-out MSE
at epoch32 improves by at least20% relative to the fixed-feature head and
training MSE improves too, without nonfinite values or actor changes. Otherwise
withhold that implementation and investigate another measured limitation.
This conditional gate is an engineering effort decision, not statistical
validation. No gameplay win claim follows from value fitting. Final acceptance
bank50000 stays reserved; reliable Hard remains unmet.

The diagnostic completed on4,767 states. Complete-game holdout has1,058
states; training has3,709. At epoch32, fixed/independent training MSE was
3.9792/2.2378 and held-out MSE12.4546/6.5086 (47.7% lower). Both held-out games
improve individually. Initial predictions and preserved actor arrays are exact;
parameters are finite. Independent review verified targets, input/output hashes,
whole-game split, equal shuffle orders/settings and the passing effort gate.
Receipt: `logs/audit/value-feature-fit-results.json`.

The comparison changes trainable capacity and the distribution of the critic
norm limit across parameters. It does not isolate the cause of gameplay losses.
Only two held-out games exist, and the winning game dominates held-out error.
This supports a bounded independent-value gameplay trial, not promotion of
an offline fitted model. Offline fits must not initialize gameplay training.
