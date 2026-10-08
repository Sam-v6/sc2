# Controlled combat-credit shaping probe

The live-count curriculum is running in its separate frozen worktree. Current
capacity shaping rewards own workers/army/bases but locally treats losing units
in a productive attack as pure loss until a much later game result. Test one
additional signal: observed cumulative enemy asset value destroyed. This is a
hypothesis about exploration/credit, not a learner bug or a new success criterion.

Use an archived source in `logs/audit/ppo-combat-source/`, separate reward-version
metadata, and two appended live score features. Add .004 times destroyed unit
and structure value (each clipped at 10,000) to the existing potential. Rewards
remain gamma*next_potential - previous_potential, with zero terminal potential.
A Marine's 50-value kill adds .2 potential, equal to its one-supply capacity.
No build order, army mix or stance timing changes are permitted.

1. Verify positive credit for a kill, no recurring positive reward for unchanged
   kill stock, and discounted telescoping through real terminal versus cutoff.
2. Warm-start from the same retained post-Medium model plus composition features,
   append zero network/Adam rows, require empty old rollout, and explicitly record
   changed reward metadata. Verify initial output/optimizer/RNG parity.
3. Run a real short smoke and confirm score fields are collected. Then compare
   40 Easy games against the concurrently running composition control, matching
   all schedules, eight workers, initial weights and original learner settings.
4. Evaluate a preserved snapshot in six frozen Hard development games under its
   matching source. Keep fresh acceptance seeds reserved. Do not promote without
   better evidence, and never mix old-objective rollouts into the new learner.

All 65 archived-source checks pass after adjusting only cloned test fixtures to
the new explicit reward context and copying the existing plot configuration.
The four real training smoke games cut off at 120 seconds with no failures.
Independent review confirms math/migration and emphasizes that the matched
curriculum must use pre-smoke bytes. Those bytes were recovered from the first
retained behavior checkpoint into `logs/ppo-combat/initial.npz`; the curriculum
uses a separate copy. The intervention is both kill observations and shaping,
so this comparison cannot isolate the reward effect alone. The migration receipt
now also hashes its script.
