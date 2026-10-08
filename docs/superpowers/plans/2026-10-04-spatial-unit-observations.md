# Observed unit type and spatial-state experiment

The compact global summary is the explicitly accepted first experiment. Hard
results remain weak; additional reward/capability probes have not established
reliable strength. Test richer live observations while keeping atomic macro
choices, micro, reward and learner settings fixed to a declared retained control.

Use protocol unit-type counts for each side and a coarse 8 by 8 playable-map grid.
Per side/cell record unit count, health, shields, ground/air weapon DPS, flying
units, structures, detectors, cloak, snapshot and current-visibility counts. These are observed
attributes, not counters for hidden enemies or scripted counter-unit recipes.
The type vocabulary follows installed UnitTypeId members; unused entries remain
zero. Normalize and clip stable feature units, record feature names in checkpoint
metadata, and make previously scouted snapshots distinct from current visibility.
Map coordinates are normalized to playable bounds; this initial grid does not
encode terrain/pathing or bind each specific type to its precise position. It is
an intermediate perception experiment, not the final unit-level agent.

1. Keep source in a separate archive; freeze it during real batches. Add tests
   that two equal-count armies differ by type, health, capability and location;
   test permutation invariance, cell boundaries and snapshot/visible distinction.
   Snapshot construction must consume only friendly and SC2-observed enemy lists.
2. Append features and migrate a retained control with zero new input rows and
   moments, preserving actor/critic/RNG/settings. Verify parity on recorded live
   observations; do not mix trajectories across feature schemas.
3. Benchmark state construction, inference and batch memory. Thousands of type
   entries are sparse; use vector accumulation rather than per-feature unit scans.
   Use existing runtimes, no installs. Retain real train/resume/frozen smoke proof
   before a matched curriculum. Compare terminal wins/losses/cutoffs and throughput.
4. Evaluate a preserved frozen snapshot on development Hard cases. Keep the same
   30-game all-race acceptance criterion and reserve the fresh acceptance seeds.
   Promote only evidence-supported functionality/strength; record limitations.

The implementation is in a separate archive, based on the detector initial
control (capacity-v1, lambda .95), so this is an observation-only intervention.
All 69 tests pass, including four new unit-state tests. Migration appends 5,418
zero rows to the existing input/Adam matrices and preserves all other context;
128 actor/critic contexts have exact parity. The resulting schema has 5,458
features, including 2,005 protocol identities per side and 11 grid channels per
side/cell. Empty vocabulary entries stay zero; sparse logged indices avoid dense
zero-filled action logs. A local synthetic 400-unit probe measured .72 ms state
construction and .043 ms NumPy inference; this is not whole-game throughput.
Real train/resume/frozen verification is next. The immutable initial and source
hashes are retained in logs/ppo-unit-state/ and logs/audit/ppo-unit-state-source/.

Real train4/resume2/frozen2 smoke checks passed, all eight were 120-second cutoffs.
A 33-snapshot controlled engine fixture exercised live observed unit types/health/
capability/spatial fields, including cloak/detection. It injects units for encoder
verification only. The prior copied add-on-production fixture failed placement;
its receipt remains retained, and no encoder change was needed for that failure.
Independent review verified 69 tests, real-context actor/critic/probability parity
and migration arrays/moments/RNG/hashes. The full Easy40 batch is now running from
untouched initial bytes with exact control build order Rush/Timing/Power/Macro/Air.

Easy40 finished2wins/14losses/24cutoffs with no failures. All opponent schedules
match and initial eight choices/times/policy seeds are identical. Full-game PPO
helpers stayed within5.22seconds. Frozen Hard6 then lost all six, no failures
or model mutation. Retain this validated encoder experiment separately; no
strength gain is established. See the combined continuation plan for next work.
