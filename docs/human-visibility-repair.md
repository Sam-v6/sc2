# Human observation visibility repair

The professional teaching data uses a 128×128 feature minimap with a scaled,
flipped world coordinate system. The Linux engine visibility guard uses native
world coordinates. Applying the native indexing to these feature maps would
wrongly reject most enemy observations. The shared player-view filter and the
tournament importer now use the appropriate geometry explicitly.

All 14 previously used teaching/development games have been re-imported into
`logs/roadmap/human-visibility-reimport-01/corpus`. Historical datasets and
reserved games were not changed or read. This work fits no model and runs no RL.

Independent verification checks source, phase, command-reconciliation and reader
bindings, exact original labels, identical own-unit observations and player/map
fields, and current enemy visibility in the supplied feature grid. It also checks
that enemy memory contains no current health, energy, orders or cooldown fields.

The verified corpus contains 7,202 command-label rows and 67,358 current enemy
observations. Every retained current enemy is in a visible source-grid cell.
Three target commands have unavailable targets, two newly unavailable after the
repair. Both newly unavailable commands use Smart (ability 1) in teaching games
163 and 1032. Keep their original commands in evidence; do not invent substitutes.
The full command encoder rejects unsupported targets with an explicit exclusion
reason. The terminal streaming inventory checked every command without fitting:
6,083 of 6,089 teaching commands and 1,112 of 1,113 development commands are
representable. The six teaching exclusions and one development exclusion all
report an unavailable observed target. The inventory took 79.1 seconds.

Re-import host CPU peaked at 9.5 percent. No GPU, new downloads or elevated system
changes were used. Original source alignment and professional partiality remain
explicit: this is not reconstruction with a matching professional game engine.
Feature-grid visibility is coarse. Passing the supplied-cell check does not prove
exact native visibility near boundaries or recover missing observations.

Evidence:

- `logs/roadmap/human-visibility-audit-01/report.json`: original geometry audit.
- `logs/roadmap/human-visibility-reimport-01/contract.json`: frozen inputs/readers.
- `logs/roadmap/human-visibility-reimport-01/report.json`: terminal import receipts.
- `logs/roadmap/human-visibility-reimport-01/verification.json`: independent checks.
- `logs/roadmap/human-visibility-reimport-01/label-inventory.json`: full representability
  inventory, terminal with explicit target exclusions.

The new corpus must replace the old paths in the next explicitly frozen teaching
contract. Do not reuse old model metrics as results on this repaired corpus.
Imitation remains paused until the scripted execution baseline passes; RL still
requires useful native imitation first.
