# Verify and expose Terran detection choices

The compact-agent experiments have not met the frozen Hard target. One concrete
action-coverage gap remains: the policy cannot choose a Raven, missile turret or
scan. Orbital energy is currently spent by the worker primitive on MULEs. Before
another broad strength run, test and expose detection as a genuine policy choice.
This is capability work, not evidence of learning or a scripted strategy.

1. Use local SC2 APIs and a controlled engine fixture to verify detector properties
   and detection of an enemy cloak case. Inventory prerequisites and current
   observation fields. Do not assume a particular Hard computer build uses cloak.
2. In a separate archived experiment, add atomic Raven production and missile
   turret construction with the normal resource/tech/placement checks. Add live
   own-detector and observed-cloak counts. A support-unit movement primitive may
   position the Raven with the chosen army stance; macro never auto-builds a
   detector or forces a unit mix. Keep the existing reward/learner settings.
3. Reproduce the missing choice with tests before implementation. Verify passive
   detector execution in the engine, legal masks, support movement, frozen RNG,
   serialization and old-schema rejection. If warm-starting, explicitly map old
   action columns by name, preserve old logits/value when new choices are masked,
   append zero observation/Adam rows, and initialize new action columns explicitly.
   Do not claim identical distributions when the new choices are available.
4. Retain pre-smoke behavior bytes, run real train/resume/frozen workflow checks,
   then a bounded curriculum and frozen Hard comparison. Existing 30-game fresh
   acceptance seeds remain reserved. Preserve source/model/replay provenance, and
   do not promote on smoke-test success or isolated wins.

This still uses compact live features as the explicitly accepted first experiment.
Later perception work should include observed unit type/health/position and spatial
information; global summary counts must not be described as the final agent.

Capability evidence: controlled two-client engine games made a stationary cloaked
Dark Templar unattackable before detection and attackable after either a Raven or
turret appeared. Both detectors reported range 11. A second fixture invoked the
actual archived legal-mask/placement/execute/micro code: Raven was unavailable
before the tech lab, turret was available with the Engineering Bay, and real
turret, tech lab and Raven construction/production completed. All three new live
features were exercised. Fixtures use injected resources/units only to test
execution; none of these games establishes learned macro or Hard strength.
Artifacts: `logs/audit/detection-engine-probe.json`, `detection-production.json`,
matching SC2Replay files, and archived `ppo-detection-source/production_probe.py`.

The archived source passes 65 tests, including two new red-to-green checks.
Migration from the retained pre-smoke post-Medium/composition model preserves old
logits/value exactly over 128 contexts and old-action probabilities within 1e-12
when new choices are masked. New columns and input rows use zero weights/moments;
old action/optimizer columns are mapped by name. Reward/learner settings remain
unchanged. The immutable initial bytes and script/source-hash migration receipt
are retained in `logs/ppo-detection/`. A separate copied checkpoint runs smoke
training, so it cannot accidentally shift the later experiment's starting point.

Matched Easy40 finished 1 Victory/8 Defeat/31 Tie, no failures. Observations
exercised both detector types and cloak. Frozen Hard6 finished 0/5/1, no failures
and unchanged model hash. No strength gain is established; retain the separate
source/checkpoint, do not promote. See experiment-results for artifact locations.
