# Human addon relocation commands and native execution

The actor-verified alias reconciler now also handles generic BuildTechLab and
BuildReactor commands. It recognizes the replay reader's producer-first spelling
through specific native catalogue names, command indexes and remaps. Every actor
must have the matching observed own producer type. Point coordinates and queue
flags are preserved. Unknown flags and mismatched point/no-target representations
remain excluded; no blanket addon exception was added.

Two new regressions reproduce rejection before the fix and pass afterward. They
check the Reactor-specific index, matching flying Barracks, wrong or missing
producer types, precise relocation targets, unsupported flags and refusal to drop
a raw point target. Full suite: 512 tests pass, 32 optional skips. Named-file Ruff
and diff checks pass.

The teaching-game rebuild now has 839 labels, adding three regular-flag addon
commands to the verified 836-label Lift/Land corpus. Independent checks preserve
all existing command labels, own observations, map, memory and unknown fields.
The new commands are Barracks TechLab at loop 7534, Starport Reactor at 7976 and
Barracks Reactor at 8112. Original events, selections, actor types, converted
point targets and precise coordinates all match. No fit or RL ran.

Four separate native fixtures isolate command behavior using debug resources and
one debug-created producer. No-target and own-position point commands build a
TechLab beside the landed Barracks. Remote point commands relocate a grounded or
flying Barracks and start a TechLab at the destination. All four commands were
accepted without raw or delayed errors. Original replay tracker starts and native
unit positions independently verify. At the 30-second cutoff the grounded remote
addon is 95 percent complete; the other three are complete. This is command
conformance, not an opponent victory. Whole-host CPU peaked at 6 percent.

| Native case | Producer after command | Addon at cutoff |
| --- | --- | --- |
| No target | Original location | Complete and attached |
| Own-position point | Original location | Complete and attached |
| Grounded, remote point | Destination | Started, 95 percent complete |
| Flying, remote point | Destination | Complete and attached |

Receipts, original replays/traces, corpora and bound source snapshots are preserved
under `logs/roadmap/addon-target-fixture-01`, `human-addon-targets-01` and
`human-addon-reimport-01`.

Five other issued addon commands still carry unsupported flag 0x1000000. Four
have a no-target converted action; one has a remote point despite an immediate
addon start beside the current producer. The source contains nine addon starts
but only eight named issued addon events. Grouped selections and delayed effects
must not become one new ticket for every selected factory or an invented ninth
issued command. The current corpus is therefore still incomplete for a faithful
full production plan.

The first three missing commands in the 600-second prefix have raw target points
exactly at their grounded actor positions and corresponding same-loop addon
starts. Native own-position/no-target equivalence supplies a specific next
conformance hypothesis: derive explicitly identified canonical execution labels
for those source effects, retaining original events/flags as provenance. Verify
that hypothesis independently before changing flag eligibility. Do not generalize
it to the later remote/grouped command, infer exact payment from a start, or teach
future effects as current observations.
