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
