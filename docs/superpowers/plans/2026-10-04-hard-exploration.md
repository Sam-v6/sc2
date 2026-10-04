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

Implementation has not started. If both remain weak, use recorded unit/action
exposure, legal production opportunities and replay behavior to choose the next
step. Low observed strength is not a runtime blocker or acceptance success.
