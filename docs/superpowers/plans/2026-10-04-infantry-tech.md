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

The immutable initial Hard30 development evaluation (seed 20000) completed
with 12 wins, 18 losses, no ties and zero failures. Every original gameplay
observation, selected action, execution result, time and reward matches the
retained parent on all 30 games. New zero upgrade fields and legal research
entries are excluded from that comparison. The greedy initial policy never
selected the new research. Receipts: `logs/audit/infantry-tech-initial-evaluate-hard30-results.json`
and `logs/audit/infantry-tech-initial-trace-parity.json`.

The bounded Hard40 continuation (seed base 30000) completed with 2 wins,
38 losses and zero failures, matching the old Hard40 opponent schedule.
All 28,160 transition reward components match the saved formula exactly.
The policy selected Stim 37 times, Combat Shield 39 and armor 40. Completed
upgrade observations occurred in 32, 33 and 40 games respectively. This
demonstrates exercised capabilities, not improved strength. Receipt:
`logs/audit/infantry-tech-hard-1-results.json`. The final checkpoint has
184 episodes/attempts and 1136 optimizer updates. Preserved SHA-256:
25c6e0c927cb2d6816a439f71b4f584f6ecf870b5ca905b906ed13d74c37ca45.
Its separate frozen Hard30 evaluation completed with zero wins, 27 losses
and 3 horizon ties, zero failures, unchanged checkpoint bytes and exact
reward components. It selected Stim once and observed it complete in one
game; no Combat Shield or armor selection occurred. Receipt:
`logs/audit/infantry-tech-final-evaluate-hard30-results.json`. This regressed
against both the 12/30 parent and the earlier 8/30 Hard40 control; do not promote. All runs use four workers,
both maps, all five fixed builds, 1200 game seconds and 300 wall seconds.
Production code remains unchanged pending strength evidence.

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

## Training drift diagnostic

On each batch's actual collected observations and legal masks, old-to-new mean
KL ranged from 0.00110 to 0.00496; collected-action ratio clip fractions ranged
from 0.00085 to 0.0339. Greedy action rankings changed on 4.59% to 20.82% of
states per batch. These descriptive checks do not establish an oversized
optimizer step as the cause. The frozen final policy selected substantially
more expansions and fewer Marines across the same 30 cases. Receipts:
`logs/audit/infantry-tech-update-drift.json` and
`logs/audit/infantry-tech-frozen-action-counts.json`. First-batch traces matched
the old Hard40 control until new research became legal, with identical initial
policy seeds; later seeds can diverge after length-dependent learner shuffles.
Receipt: `logs/audit/infantry-tech-training-first-batch-parity.json`.

The best retained policy remains kills-only Easy40 at 12/30. The research
implementation works but this continuation is not stronger. Reliable Hard
strength and the untouched fresh-bank evaluation remain open.
