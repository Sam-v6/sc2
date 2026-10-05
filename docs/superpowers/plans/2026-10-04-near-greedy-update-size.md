# Fixed-batch update-size diagnostic

The near-greedy continuation collected more training wins and scored 14/30 on
reused development cases, but lost its new-bank comparison to the retained
parent (11/30 vs 13/30). It is not promoted. The first update had a much larger
mean distribution KL than later batches (0.236 versus 0.0014–0.0131). This does
not establish that update size caused the weaker generalization.

Before spending more game simulations, reconstruct that exact first batch from
its saved frozen behavior model and actual action/reward logs. Preserve the
original RNG after its four worker seeds, counters, masks, lambda-one returns,
Adam moments, observations, reward and temperature. Reproduce the recorded update
at learning rate 0.0003; compare numeric parameters/moments with the next saved
behavior model and report any reconstruction error.

On a separate copy of the same on-policy batch, change only learning rate to
0.000015 (20 times smaller, matching the inverse temperature scale). Run the
same helper/shuffle/epochs and measure distribution KL, sampled likelihood
clipping and greedy flips on those collected states. This is an offline numerical
diagnostic, not a new trajectory, win prediction or strength evidence. Do not
change production source or existing experiment inputs.

Only if reconstruction reproduces the recorded control and the smaller update
substantially reduces distribution movement should a separate, explicitly
migrated source/context and bounded training experiment be considered. No training
is authorized by a mere offline win claim. The reliable Hard target and reserved
acceptance bank remain unchanged.

## Verified diagnostic and bounded continuation

Control reconstruction matches the next recorded checkpoint's parameters and
moments to at most 2.78e-16, with exact metadata/RNG. On the same 2,573 states,
reducing learning rate 20 times lowers mean KL 0.23577->0.000847, selected-action
clip fraction 15.08%->1.13%, and greedy flips 8.39%->0.66%. Independent review
confirmed reconstruction and metrics, finding no material defect. Receipt:
`logs/audit/near-greedy-update-size-results.json`.

All four diagnostic episodes were defeats. The result says nothing about winning
batches or subsequent state distributions. The learning rate applies to all Adam
parameters, including the critic head, so value fitting also slows. This remains
a hypothesis to test in actual training.

The isolated source changes only `settings.learning_rate` from 0.0003 to 0.000015.
The old-rate rejection test failed before implementation; all 86 tests then pass,
including real Torch contextual learning/resume and strict temperature context.
Source: `logs/audit/ppo-near-greedy-small-update-source`. Metadata-only migration
uses the untouched near-greedy initial, retaining all numerical arrays, counters,
RNG, moments and other metadata. It does not use the failed trained final.
Receipt: `logs/ppo-near-greedy-small-update/migration.json`. Initial SHA-256:
0eb20f2d9afb27a2df0e077c0c4808b8da274fc72649a72f49ccc50ecc803896.

Complete separate two-game train/resume/frozen checks before training. Then run
exactly 40 Hard games from the untouched initial at seed base 30000, both maps,
all races/five builds, four workers, cadence one, 1200 game seconds/300 wall
seconds. Preserve batch models; stop on runtime/learner failure and audit rewards,
returns, source context, optimizer payloads and schedules against the retained
original-rate control. Do not alter settings mid-run.

Freeze the final and evaluate greedy Hard30 separately on development banks
20000 and 40000 using the same documented opponent cases. Prefer this candidate
for further work only if it reaches at least 14 wins on the reused bank and at
least 13 on the new bank, matching the better observed reference in each bank.
This is an effort-allocation gate, not statistical proof. If it fails, retain
the old baseline and do not extend this arm. The unchanged reliable Hard target
and reserved final bank 50000 still govern acceptance.

Independent review verified the sole learning-rate source change, exact migration,
prior-context rejection and 86-test result, finding no material defect. Separate
two-game train/resume/frozen sampled checks finished with zero failures (all six
120-second horizons). Optimizer state advanced 676->684 updates; resume hashes,
finite arrays, context/cadence and unchanged experiment inputs were verified.
Receipt: `logs/audit/near-greedy-small-update-smoke-results.json`.

The bounded Hard40 continuation is now running from the untouched experiment
initial, not the smoke model. Production source and the retained baseline remain
unchanged.
