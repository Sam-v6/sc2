# Early human addon builds: verified execution equivalence

Three early addon commands in the winning human game now have explicit canonical
API labels. The raw commands carry flag 0x1000000 and target the exact position
of a complete landed Barracks. Converted actions have no target. Each command
has one selected matching producer, one converted action, and one matching own
addon start beside it in the same loop. The native fixture independently proves
that a no-target or own-position addon command builds beside a landed producer.

`addon_conformance.in_place_addon_label` requires that narrow combination. It
rejects remote targets, flying/incomplete/foreign producers, multiple selected
matching producers, wrong command indexes, other flags, and missing/ambiguous
same-loop starts. It does not interpret the flag or relax the ordinary reconciler.
Raw events, flags, actor position, selection and tracker evidence remain in each
new label's `label_translation` and the dataset receipt. These are identified
execution-equivalence labels, not literal translations of every replay flag.

The fresh teaching corpus has 842 labels. Independent verification preserves all
839 previous labels, their commands, own observations, map and memory. New labels
are Reactor at loop 2837 and TechLabs at 4000 and 5164. Their new addon tags are
absent from the pre-effect decision observations. Tracker effects validate the
labels only; provenance is outside `observation` and must never enter model
inputs. Raw source events, native converted actions, selections and positions
are independently reconstructed. Converted action identities are unique and
not reused by existing labels. The two later flagged/grouped commands remain
unresolved.

Two new regressions cover equivalence and rejection boundaries. Full suite:
514 tests pass with 32 optional skips. Named-file Ruff and diff checks pass.
No new native game, training or RL ran in this step. Exact source, new corpus,
audit and independent verification are preserved under
`logs/roadmap/human-in-place-addon-reimport-01`.

A preliminary 600-second prefix screen now finds 201 matched macro-family
commands and 41 unresolved events with native macro candidates. Most concern
unit transformations or Depot raising/lowering, but important candidates include
one Viking training command, one Refinery, research and cancellation. Candidate
proximity is not identity proof. The screen is preserved under
`logs/roadmap/human-production-prefix-01`; it is descriptive, not an independently
accepted full-plan gate. Next resolve these specific name/index/target mismatches
and classify optional combat-mode versus production dependencies before compiling
the fixed winning-human executor. No complete-plan, payment-attribution or learned
strength claim is made.
