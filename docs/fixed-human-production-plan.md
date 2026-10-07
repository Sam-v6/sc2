# Fixed winning-human production plan

Game 870 (Clem, Terran versus Zerg, human win) now has a compiled first-600-second
production command plan. This is fixed human-plan playback preparation, not a
trained policy, and it has not yet been played natively.

| Instructions | Count |
| --- | ---: |
| Train units | 112 |
| Build structures/addons | 47 |
| Lift | 15 |
| Land | 14 |
| Cancel last queued production | 6 |
| Research | 6 |
| Morph Command Centers | 3 |
| Total retained instructions | 203 |

Four additional commands already had the same order before and after issue,
without a queue-count increase: three SCVs and one Hellion. They remain in the
artifact as source evidence and are not counted as four new work instructions.
Six actual structure Cancel Last commands remain in the plan; combat cancellation
on a Cyclone is outside the production compiler.

The compiler retains original loop/sequence order, full actor tags, target tags
and flags. Generic Lift/Land/addon aliases resolve to unique actor-specific native
abilities; generic research aliases resolve to exact source research levels using
the previously verified producer metadata. Ambiguity produces an explicit
unresolved row instead of a guessed instruction. All 207 retained/repeated source
rows resolve without ambiguity.

Queue flags and point coordinates are independently checked against original raw
events. The original fixed-point coordinates are decoded using 4096 units per
tile. In this actual plan all point coordinates already match the imported values;
no coordinate corrections were necessary. The compiler nevertheless preserves
the original precision, with a test for half-tile coordinates and queue recovery.
The three verified no-target addon equivalences remain no-target commands.

Independent verification checks source actor/target identity, canonical ability
equivalence, original specific indexes, queue flags, precise coordinates, event
uniqueness/order, repeated-order classification and input hashes. Final artifact
and source snapshots are in `logs/roadmap/fixed-human-production-plan-02`.
Full suite: 530 tests pass, 32 skipped; named-file Ruff passes.

Important limits remain: unmatched source commands and combat/Depot mode changes
are outside this compiler, original and installed Acropolis map bytes differ, and
issued commands do not prove payment or completion. Native playback still needs
initial and newly built source/native entity binding, physical placement and
landing-site checks, target translation, cancellation handling, and a declared
timing/divergence rule. Use the verified mining/combat primitives for execution
assistance. Retain addon identities through the transfers documented in
[the topology result](human-producer-topology.md). Do not add scripted production
quotas, treat future source outcomes as observations, or restart fitting/RL from
this offline result.
