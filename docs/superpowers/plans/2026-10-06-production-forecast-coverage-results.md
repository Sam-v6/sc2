# Human production forecast coverage result

The frozen six-game coverage audit is closed. No training, checkpoint change,
native game or RL occurred. This changes the next action: repair and verify human
production label coverage before another full-controller fit.

Source-bound audit:
`logs/roadmap/production-forecast-coverage-01/audit.json`, SHA256
`b1c5b0f044c03331dfeaba8e0e47a20b58066fd23c6c80a553b30c5b6f2df5fe`.
All 3,400 labels independently reconstruct with a direct forward scan. Observation
contents and source bytes remain unchanged; original corpus bindings match.

| Label coverage | Count |
| --- | ---: |
| Immediate Build/Train/Research commands | 850 |
| Usable current-or-next production labels | 2,069 |
| Censored because an unresolved command intervenes | 1,322 |
| Censored because no subsequent production command remains | 9 |

| Ability | Immediate decisions | Forecast observations | Unique future decisions |
| --- | ---: | ---: | ---: |
| SCV | 355 | 917 | 355 |
| Supply depot | 83 | 192 | 83 |
| Barracks | 18 | 40 | 18 |
| Marine | 162 | 362 | 162 |

1,987 usable labels are within five seconds of the production command. Per-game
median remaining time ranges from zero to 0.80 seconds; p90 from 2.41 to 4.51.
These command-time observations densify supervision modestly, especially for
Barracks. They do not create independent demonstrations, establish useful advance
planning, or show that the model can predict these targets. The taxonomy omits
other macro abilities, including morphs, and does not restrict the raw controller.

A separate read-only diagnostic binds the existing command reconciliation names,
catalogs and corpus receipts:
`logs/roadmap/production-forecast-coverage-01/unresolved-names.json`, SHA256
`5ae5151025f9fa04e76406da45e3f495e49afdf46904e6123749f6a5a5b6ed8d`.
Across the six games, 1,276 issued commands remain unresolved: 1,110 lack a mutually
unique verified converted command, 122 lack known human selection, 34 have
unsupported flags and 10 have unknown replay ability names. Reapplying the current
exact normalized name/index test finds 900 without an engine catalog match and
376 with a unique match. A unique name alone does not recover a complete command.

Missing names include production: TrainViking, BuildSiegeTank, BuildHellion and
BuildBarracksReactor, alongside Gather/ReturnCargo/rally and other controls.
This is evidence for an identity/coverage audit, not permission to guess mappings.
An exploratory sc2reader check uses its 70154 fallback datapack for these 76052
replays; its unit numeric IDs differ from raw engine IDs. Do not directly join those
IDs or claim exact version fidelity. Investigate independent producer unit names,
engine production metadata, command indexes and retained-command corroboration.
Keep uncertain actor/target/flags and observation chronology unresolved.

Validation: focused label tests pass; full normal suite passes 395 tests with 31
optional skips. Ruff and diff checks pass. Independent review found no blockers; its median
calculation note was fixed and the audit rerun with the corrected statistic. Current label implementation is an
auxiliary supervision tool, not a learned policy or native competence result.

Next: freeze a bounded production-identity audit, quantify which missing human
production decisions can be proved from existing local sources, and only then
choose an imitation experiment. RL and the reserved replay evaluations stay off.
