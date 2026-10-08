# Observe every supported Terran combat unit

The atomic action interface supports Reapers, Hellions and Vikings, but the live
state omits their counts. Equal-supply armies of these units can alias. Append
three counts, preserving existing feature order and the reward/action interface.
The compact state remains a first experiment rather than the final perception.

1. Reproduce the alias using live snapshot extraction, including transformed
   Hellions/Vikings. Check old checkpoints fail the strict schema guard.
2. Append scaled counts and extract both forms. Do not change rewards, actions,
   micro, encoder normalization or learner settings.
3. Run all tests and independent review. For an explicitly recorded PPO warm
   start only, append zero input weights/Adam moments to a retained empty-rollout
   checkpoint. Verify output parity, preserved optimizer/RNG/context and record
   parent hash and changed schema. Keep old frozen tests under old source.
4. Check a short real train/resume/frozen loop, then run a bounded Easy curriculum
   and frozen Hard development comparison. Do not infer strength from cutoffs or
   training wins. Keep the fresh acceptance bank unused until development improves.

Regression results: five Hellions and five Vikings produced identical encoded
live snapshots before the fix. The new test distinguishes them and checks
Hellbat/Viking assault forms. All 63 checks pass; independent review found no
defects. The explicit warm start uses the retained post-Medium PPO checkpoint
(parent SHA `4219cc29117ba39d067732cffdf34b22bbeb9cf175f70aec1b1ded350a695af4`).
Zero appended rows preserve logits/value exactly for 128 states, even with
nonzero new feature values; all other weights, moments, counters, RNG, cadence,
reward and settings are retained. Audit script/receipt are retained under
`logs/audit/migrate-composition.py` and `logs/ppo-composition/migration.json`.
The pre-training migrated bytes are retained in `logs/ppo-composition/initial.npz`.
A separate real Medivac execution probe healed a Marine to full health under
current movement micro, so no speculative healer fix was made. Its controlled
current/attack-move/explicit-heal traces live in `logs/audit/medivac-probe.json`.

Real migrated PPO smoke checks completed four train games, two resume games
and two frozen games without failures; each cut off at 120 seconds. Resume
advanced the inherited 64-episode model to 70 episodes/attempts and 812 updates,
while frozen evaluation preserved the exact checkpoint bytes. These checks
establish workflow compatibility only. Evidence folders:
`logs/ppo-composition-{smoke,resume,frozen-smoke}/`.
