# Production metadata recovery and live research repair

The winning human teaching game now has 851 labels, with nine more production
instructions recovered since the verified 842-label corpus. All previous labels,
commands, own observations, map and memory remain unchanged. No training or RL ran.

Eight labels are Viking/research commands. The reader calls the trained unit
Viking; the native catalogue names it VikingFighter. Exact native training index
4 resolves that name. Research uses independently named upgrades and specific
command indexes. Vehicle weapons have numbered legacy reader names. Vehicle/ship
armor upgrade metadata points to inactive legacy abilities; matching catalogue
names and the original index identify unique active abilities instead. Generic
vehicle research additionally requires every observed actor to be an Armory.
Independent checks reconstruct original reader metadata, catalogue relationships,
converted actions, actor types, selections and flags. The eight additions are one
Viking, Cyclone lock-on damage research, three vehicle weapon levels and three
vehicle/ship armor levels.

The initial research rebuild recovered five labels; its missing armor aliases
exposed the inactive pointer. Its bound source is preserved under
`human-research-reimport-01`. The corrected, independently verified corpus is
`logs/roadmap/human-research-reimport-02`, with 850 labels.

The ninth label is the Refinery at loop 13280. Its original neutral snapshot has
zero target tag and a retained point of (113.5,53.5). The converted command targets
one SpacePlatformGeyser snapshot at that point; the original map tracker contains
one matching initial neutral geyser. The reader's snapshot type-number vocabulary
is incompatible, so that number remains uninterpreted. The target label is
recovered from geometry and named map/resource identity, with original provenance.
It remains a fog snapshot, absent from current visible-unit inputs. The label
explicitly marks `target_observed=false` and requires a representation check.
No current contents or visibility are invented. A raw-command fit must supply
verified neutral-terrain memory or exclude this target argument; label recovery
alone does not establish sensory readiness. Initial visible-only validation
rejected this actual snapshot; the corrected test explicitly distinguishes a
static snapshot from current visibility. Independent replay/record verification
preserves all 850 labels and confirms the unavailable target and unchanged inputs.
This corpus and source are under `human-refinery-snapshot-reimport-01`.

The same inactive armor pointer also broke live goals: `goal_catalog` selected
2297, which is unavailable and cannot match an Armory's available research. It now
requires a unique active ability with the same catalogue name for an inactive
upgrade pointer. Missing/ambiguous replacements fail explicitly. A regression
reproduced the old ineligible Armory and passes after the fix.

A fresh eight-second debug fixture verifies the repair against the actual engine:
2297 is inactive; 864 is active, available, accepted once and produces a research
order whose progress rises across 21 observations. No raw/delayed errors. Sampled
whole-host CPU peaks at 2.7 percent. This is accepted research and order progress,
not completed research, opponent strength or learning. Linux native queries/orders
retain specific 864 while the converted Windows source uses generic 3700.
Cross-source research-level queue accounting remains to check before claiming a
complete production executor.

The first fixture used a hardcoded seed differing from its job; it is archived
under `upgrade-pointer-fixture-01` and not credited. The corrected02 fixture reads
the declared job seed, independently confirmed in replay userInitialData. Initial
verifier assumptions about generic order IDs and the replay seed field were
corrected without restarting the02 game. Its final receipt and exact source are
under `logs/roadmap/upgrade-pointer-fixture-02`.

Full suite: 522 tests pass, 32 optional skips. Named-file Ruff and diff checks pass.
Next verify cancellation identity, classify combat/Depot mode changes, and audit
producer/addon binding and research-level queue accounting for the fixed human
production test. Retain the snapshot-target limitation for later raw-command
imitation. The full learning roadmap remains incomplete.
