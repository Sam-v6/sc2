# Direct Hard learning and controlled exploration

Equal Easy continuations yielded 3 control wins versus 6 with richer inputs, but
both froze at 0/6 Hard. The separate stance mask/command probe also lost all six;
no default change is warranted by those outcomes. The earlier finite Easy40
snapshot has 2/30 Hard development wins, both Zerg Air. Retain that known starting
actor rather than adopting a continuation that improved only Easy outcomes.

1. Use the untouched finite/spatial migrated initial checkpoint (finite Easy40
   actor/critic plus zero unit-state input rows), not smoke or failed Easy80 models.
   Both branches share richer observations, reward, primitive actions/micro and
   initial counters/RNG. Keep original stance behavior for this comparison.
2. Archive a candidate with categorical softmax temperature 2 while the control
   stays at 1. Record temperature in checkpoint settings. Apply it consistently
   to NumPy inference/rollout probabilities and Torch PPO likelihood gradients;
   the critic target/value is unchanged. Explicitly migrate old parameters and
   moments/context without pretending sampled distributions are preserved.
   Frozen argmax choices should initially remain identical for positive temperature.
3. Add mathematical distribution/gradient/parity/context tests, run the full suite
   and real train/resume/frozen smoke separately from untouched inputs. Preserve
   metadata/source hashes. Never mix rollouts across temperature/source contexts.
4. Train 40 Hard games per branch on matching all-race/five-build/two-map schedules
   with eight workers. Retain per-batch weights; report true wins/losses/timeouts
   and failures. Higher exploration can lower initial performance; compare actual
   terminal outcomes and exercised production branches, not entropy alone.
5. Freeze and evaluate matching development cases, broadening promising snapshots
   to 30 games. Keep the fresh acceptance bank reserved and existing reliable
   all-race Hard win-rate target. No macro recipes or scripted timing are added.

The separate temperature source is implemented and passes 75 tests. If both remain weak, use recorded unit/action
exposure, legal production opportunities and replay behavior to choose the next
step. Low observed strength is not a runtime blocker or acceptance success.

Initial-distribution inspection over 4,603 logged Hard states found broad sampling
probabilities already present at T1: Starport probabilities sum 377.18 across 2,987
legal states, despite never being selected by the frozen argmax policy. T2 raises
that sum to 412.99 and slightly raises average entropy 1.436 to 1.448. These are
conditional probability sums on old states, not predicted commands or victories.
This evidence also motivates frozen seeded sampling checks of the learned PPO
distribution alongside argmax; the win-rate/opponent scope remains unchanged.

Three temperature tests were added red-to-green, and a deliberate NumPy-only
change made the existing Torch integration fail before helper correction.
Independent review confirmed 75 tests, preserved arrays/moments/RNG/context/hashes
and consistent temperature-scaled likelihoods/autograd. Raw logits, critic and
frozen argmax are unchanged; entropy/gradients and sampled distributions change.
Real train 4/resume 2 smoke completed without failures, all 120-second cutoffs;
frozen 2 verification also completed without failures and preserved checkpoint bytes. Untouched initial bytes are copied separately for
the paired Hard40 runs. Artifacts: logs/ppo-temperature/, logs/ppo-temperature-smoke/,
logs/audit/ppo-temperature-source/, temperature-probability-exposure.json.


The main CLI now exposes `--mode sample` for frozen, seeded PPO categorical
sampling. It forces epsilon to zero, rejects DQN, collects no training rollout,
and verifies unchanged checkpoint hashes. A concurrent-replacement regression
failed before extending the greedy hash guard. All 67 main tests pass; independent
review confirmed the fix. Two real 120-second Easy games ended at the cutoff,
without failures or checkpoint changes, after the fix. This proves execution and
immutability, not playing strength.

Direct Hard training control completed 40 attempts: 0 wins, 38 defeats, 2 cutoffs.
Temperature 2 stopped after 32 attempts: 31 defeats and one SC2 WebSocket startup
ServerDisconnectedError (Terran Air, Simple64, seed 139), before bot decisions.
The remaining eight scheduled attempts resumed from the archived source and
completed with eight defeats and no failures. Thus T2 has 39 completed games and
one engine failure across 40 attempts; it is not a clean 40-game paired outcome
comparison. Preserve the failure, exclude it from game outcomes, and do not
silently replace its seed or treat it as a loss. No source changes or recipe
changes were introduced to complete the schedule.

The untouched initial policy's frozen sampled Hard six all lost, with no failures
and identical checkpoint hashes. Next freeze both direct-Hard trained candidates
and evaluate six greedy and six sampled games each on the same development
seeds/races/Rush-Macro cases. No model is promoted on these training outcomes.
