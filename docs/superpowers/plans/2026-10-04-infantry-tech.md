# Infantry research capability experiment

The retained kills-only Easy40 policy remains strongest at 12/30 frozen Hard
wins. More Easy, Medium and Hard continuations scored 2/30, 2/30 and 8/30.
Research capability is a concrete restriction: the current macro space cannot
choose Stim, Combat Shield or infantry armor. That does not prove these omissions
caused the losses. Extend those atomic choices while keeping research decisions
learned and retaining the original combat movement/stance behavior.

## Verification and comparison

1. In an isolated source archive, add three completed-upgrade observations and
   three resource/producer/progress-gated research actions. Existing research
   remains atomic. Add local Stim activation only after policy-selected research,
   for healthy Marine/Marauder units facing a visible, attackable, in-range
   ground threat without an active Stim buff. No build order, unit mix,
   research timing or attack timing is prescribed.
2. Verify research commands and completed states in real SC2 debug fixtures:
   shield maximum health, Stim buffs/health costs for both infantry types,
   armor level and ordinary command eligibility. Debug cheats speed these
   capability checks; fixtures never enter training or strength totals.
3. Record migration from frozen Easy40: every existing named parameter/moment,
   RNG, counter and reward/optimizer/cadence context is preserved. New scalar
   weights/moments are zero. New research heads copy the existing infantry-
   weapons research prior; their moments are zero at the inherited global Adam
   step. Verify old logits/critic on retained observations and strict new schema.
4. Complete isolated train/resume/frozen smoke checks. Then compare the immutable
   migrated initial policy on the same Hard30 cases and run one bounded Hard40
   continuation, matching the retained parent/control opponent schedule. Preserve
   initial/final bytes and sources; evaluate the trained final snapshot separately.
   An initial capability gain is not evidence of additional RL learning.
5. Keep the 70% frozen Hard30 target and untouched final seed bank. Do not promote
   based on fixtures, updates, commands, offline rankings or training outcomes.

## Current evidence

The isolated implementation passes 84 tests. Three real fixtures completed all
research; shield gives Marine maximum health 55, both infantry Stim abilities
activate with the appropriate buffs/health costs, and armor level becomes one.
Archive: `logs/audit/ppo-infantry-tech-source`; fixtures:
`logs/infantry-tech-fixture/{capabilities,automatic-stim,automatic-stim-both}.json`.

Migrated schema: 5,463 features, 30 actions. Initial SHA-256:
35f9c7fbff1e66eba14bbd3b95c573662c2d1aef24447578f891e93c8164e149.
Every old named parameter/moment is exact. On 406 retained states, old-logit
error is 4.44e-16 and critic error 2.22e-16. Receipt:
`logs/ppo-infantry-tech/migration.json`. Separate two-game 180-second train, resume and frozen evaluation checks
completed with zero failures (all horizon ties). The resumed smoke advanced
from 676 to 692 optimizer updates across four games, preserving cadence and
checkpoint chaining; frozen evaluation left initial bytes unchanged. Receipt:
`logs/audit/infantry-tech-smoke-results.json`.

The immutable initial Hard30 development evaluation (seed 20000) and bounded
Hard40 continuation (seed base 30000) are running with four workers each,
both maps, all five fixed builds, 1200 game seconds and 300 wall seconds.
The continuation starts from the unmodified migrated initial policy, not the
smoke checkpoint. Production code remains unchanged pending strength evidence.

## Withheld cooldown prototype

The independent ranged cooldown/focus prototype passed 86 tests but performed
worse in controlled debug fights. Against 3 Roaches, the six-Marine control killed
one before losing all six; the prototype killed none. Against 12 Zerglings, the
control killed all twelve with five Marines surviving; the prototype lost all
six Marines after killing six Zerglings. Initial observations were not identical,
so these two pairs are limited evidence, not a causal strength estimate. This
is sufficient to withhold promotion and broad training of the prototype.
The first computer-controlled fixtures also lost visibility when the AI regrouped;
that was not proof of death. A second minimal opponent bot kept the actual units
fighting; tracked death tags verified resolution. All artifacts are preserved in
`logs/ranged-micro-fixture*` and `logs/audit/ranged-micro-controlled-results.json`.
The infantry experiment does not include this prototype.
