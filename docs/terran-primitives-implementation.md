# Terran primitives implementation and native development checks

The controller is explicitly scripted. No professional-imitation fit or RL runs
in this phase. Its role is to prove execution before reconnecting human decisions
and eventually RL. It does not replace the broad raw-command learning roadmap.

`src/bots/terran_primitives.py` contains worker assignment, target compatibility,
cooldown movement, tank transformations, order deduplication and destination
arrival checks. `scripted_targets` is the separately named baseline strategy.
`src/bots/primitive_terran.py` connects these rules to native SC2: protected
builders, interrupted construction, repairs, worker/Marine/Tank/Medivac/Viking
production, supply, expansions, addon clearance, upgrades, MULEs, scouting,
defense, attacking and searching after clearing an area. Combat runs every eight
game loops; macro runs every 24 loops. Income, commands, action failures and
player observations are recorded alongside replays.

The CLI accepts `--bot primitives`. Use one worker for local diagnostics. The
saved panel harness additionally applies the host CPU guard; the generic CLI
does not impose that guard by itself.

## Verification so far

- Worker and combat regression tests were observed failing before implementation,
  then passing. They include gas redistribution, protected builders and returning
  workers, ground/air targeting, cooldown movement, tank siege behavior, hidden
  enemy exclusion, stragglers at attack destinations and duplicate orders.
- The opt-in native test runs a four-minute VeryEasy game and checks collected
  income, worker growth, military production and replay/trace output. It passes
  after the visibility repair. This is an engineering smoke test, not strength.
- The latest full suite passes 450 tests with 32 optional skips. The opt-in native
  test was run separately. Ruff and diff checks pass.
- Generic SDK TechLab aliases now take the addon-pad placement path instead of
  treating a no-target command as a point-target building command. The native
  smoke test caught the original exception and passed after the repair.

## Stopped first panel and visibility defect

`logs/roadmap/primitives-native-01/panel` preserves the original frozen source,
contract, traces and receipts. Three games finished before interruption: Terran
Rush and Macro reached the 1,200-second cutoff; Zerg Rush produced a victory at
562.9 seconds. The panel was intentionally stopped, with session exit code 130.
These results are not credited toward the Hard baseline.

The saved Terran Rush observation includes an enemy Missile Turret with protocol
display type Visible and current health, but the visibility-grid pixel at its
position is zero. The installed Burny SDK already guards this older Linux engine
behavior with the grid. Our shared `PlayerView` only checked display type.
It now checks the grid when supplied, excludes fog entities from current inputs,
retains previously observed memory without refreshing its location/time/health,
and does not create memory from a newly encountered bogus Visible flag. When a
source has no visibility grid, display-type filtering alone cannot prove that
source is safe against this engine defect.

This finding also requires an audit of earlier native/human source observations
before another fit. Earlier display-type tests and integrity receipts are not
proof against this newly identified defect. Existing geometry/production records
remain diagnostic evidence; earlier learned strength must not be attributed to
an independently proven fog-safe controller without that audit.

The first panel also exposed attack-search stalling: in Terran Rush, most Marines
had reached the target, but distant Tanks kept the army center just outside the
eight-tile threshold. Arrival now requires a majority of attackers nearby,
rather than the average position of every attacker. Duplicate unchanged attack
orders and orders to wait at an already reached destination are suppressed.
Construction failure codes 44 and 208 remain to investigate if they recur after
the repaired panel. Do not claim every primitive is reliable yet.

## Completed development checks and current candidate

Both `logs/roadmap/primitives-native-02/panel` and
`logs/roadmap/primitives-native-03/panel` are terminal and independently verified.
Each preserves its contract, source snapshot, original replays, traces, static
catalogue and verification receipt. Both requested API Hard (protocol value 5);
the older engine names its opponent “A.I.1 (Harder)” inside replay metadata.
This discrepancy is recorded rather than silently changing the requested level.

| Panel | Terran Rush / Macro | Zerg Rush / Macro | Protoss Rush / Macro | Host CPU peak |
|---|---|---|---|---:|
| 02 | Victory / cutoff | Victory / cutoff | Victory / Victory | 19.9% |
| 03 | cutoff / cutoff | Victory / Victory | Victory / Victory | 7.7% |

Panel 03 excludes untargetable KD8 charges, requires detected direct targets,
respects Tank minimum/maximum range and transformation orders, caps Tank
production relative to Marines, returns the scout to mining, adds Viking air
coverage, and checks builder reachability before selecting a placement. Its six
games produced zero raw action failures and eight delayed errors, all in Zerg
Rush. This improved action legality but did not increase the overall win count.

Terran traces show continuing Marine production and a depleted ground army still
travelling to the enemy base. The attack flag used total army supply, including
healing and air support. The current candidate starts/resumes attacks based on
Marine/Tank strength, regroups after ground losses, excludes dead actors, and
keeps Vikings near the ground army unless visible aircraft need engagement.
These are explicit scripted strategy/control choices, not learned decisions or
permanent restrictions on the human action space.

`logs/roadmap/primitives-native-04/panel` is a terminal, independently verified
two-game Terran recheck of that candidate, using the same Rush/Macro seeds and
bounded contract. Rush lost at 1,029.6 seconds; Macro timed out at 1,200 seconds.
Host CPU peaked at 5.5 percent. Both games had zero raw action errors; Macro had
three delayed errors. This candidate did not improve strength. Saved Tank
positions stay near home despite enemy-base attack orders, so movement and
production exits need direct diagnosis before more strategy changes. Its smoke
test passes; the full suite ran 450 tests successfully with 32 optional skips.
No source bound by the panel is edited during execution. Verify original replay
outcomes, actual production, sampled fog/weapon compatibility and error counts
before interpreting results.

These development panels do not satisfy the 30-game acceptance gate. Broader
strategies and fresh seeds/maps remain necessary. Only after reliable scripted
execution and the baseline gate should professional imitation resume; RL follows
useful native imitation. Historical observations require the Linux fog audit
before reuse in fitting.

## Tank exit diagnosis and spacing repair

Native replay path queries at 420/540/660/780 seconds compared living Tanks and
Marines at the same external defensive coordinate. Every sampled Marine had a
positive path; every sampled Tank returned zero. All Tanks could reach the local
rally point. The enemy base center returned zero for both unit types early in the
game, so that coordinate alone is not evidence of trapping. The external-point
control and persistent home positions establish the size-dependent blockage.
Artifacts: `primitives-native-04/tank-marine-path-diagnosis.json` and its saved
query harness/output. No privileged enemy information enters the controller.

Construction now reserves a two-tile lane around physical structures and addon
pads, including pending and same-batch builds. Lowered depots and flying buildings
are traversable and excluded from existing physical reservations. The previously
unused unit catalogue identifies structures and actual creation footprints.
Both scripted and human-goal execution use the same spacing calculation. This is
physical execution assistance; it does not choose a human macro strategy.

Panel 05 is terminal and independently verified: Terran Rush Victory683.2seconds,
Terran Macro Victory836.8seconds, zero raw/delayed action errors in both games,
peak hostCPU8.9percent. The fixed Rush replay has positive external-point Tank
paths at420/540/660seconds and Tanks at the enemy side by the end. This supports
the specific movement repair; it does not prove every possible production layout.
The full suite ran452tests with32optional skips; native smoke passed separately.

Panel 06 runs the unchanged candidate against all six previous race/build jobs,
with the same CPU guard and bounds. After its terminal receipt run
`logs/roadmap/verify_primitives_native_panel_06.py`, preserve the bound sources,
and inspect any failure before a fresh all-race acceptance panel. Imitation/RL
remain paused.

## All-race recheck and fresh baseline contract

Panel06 and its verifier are terminal: six victories, peakCPU13percent. All raw
failures are reconstructed: one in Terran Macro and371in Protoss Rush. Protoss
failures all attempted to attack an invulnerable AdeptPhaseShift. That temporary
unit is now excluded alongside KD8Charge from direct targets, with a meaningful
failing-then-passing regression. Neither exclusion restricts meaningful human
control. Full suite454tests/32skips; separate native smoke passes.

`logs/roadmap/primitives-hard-baseline-01/panel` is the fresh frozen30-game panel.
It has ten games perrace; Rush,Timing,Power,Macro,Air on bothAcropolisLE and
AbyssalReefLE; seeds819001–819030; step8;1,200game seconds/300wall pergame;
sequential CPU-only execution and the existing80percent guard. All jobs and
thresholds were frozen before results. Initial scripted acceptance requires
at least21/30overall and7/10perrace. Report each build/map as well; this panel
does not prove universal strength, and higher difficulty/micro transfer/human
imitation/RL remain unfinished. No source bound by this panel may change while
it runs. Save its original artifacts, run its verifier, then inspect failures.

## Human visibility compatibility prerequisite

The offline audit covers7,202existing teaching/development states and73,724current
enemy observations; reserved games were not read. Treating their128×128feature
minimaps as native coordinates would reject68,861enemies. Correct scaled/flipped
coordinates place67,358on visible cells,6,366on nonvisible cells, with1,429having
no visible immediate neighbor. Coarse boundary cells cannot prove actual enemy
invisibility. See `logs/roadmap/human-visibility-audit-01/report.json`.

PlayerView now accepts explicit feature-world dimensions, and the tournament
importer supplies them to use the documented flipped/scaled geometry. Native
callers retain native grid handling. An integrated converter regression verifies
a visible enemy, then hiding its cell without leaking health through memory.
This guards future imports; it does not retroactively repair saved datasets.
Re-import into new directories, verify original label/phase/source bindings and
fog/memory accounting, and handle unsupported targets explicitly before fitting.
Do not overwrite historical corpus evidence or claim it is repaired already.

The required human re-import and independent verification are now terminal in
`logs/roadmap/human-visibility-reimport-01`. All 7,202 labels and own-unit fields
are preserved. Full encoding inventory reports 6,083/6,089 teaching and
1,112/1,113 development commands representable; seven unsupported target labels
are explicit exclusions. See [the source repair](human-visibility-repair.md).
This completes the observation/label engineering prerequisite for a new fitting
contract; it does not establish imitation quality or native game competence.

## Initial scripted baseline accepted

The fresh 30-game panel and independent verifier are terminal: 30 victories,
10/10 per race, 15/15 per map and 6/6 per named build. Peak host CPU9.3 percent.
See [the result and remaining limitations](scripted-hard-baseline.md). Frozen
source is preserved; subsequent Graviton Beam guard verification is separate.
Full suite455tests/32optional skips and native smoke pass after that guard.
No human fit or RL ran in this phase. Reconnect verified primitives to human
choices next; the broad-action learned-policy roadmap remains unfinished.

### Liberator ground-mode execution (2026-10-07)

The shared combat helper now deploys/holds/undeploys Liberator ground zones.
Design reference: [Sharpy's Liberator controller](https://github.com/DrInfy/sharpy-sc2/blob/d9577a00ee47634b56ff7ee0740c6ed3043659a2/sharpy/combat/terran/micro_liberators.py),
MIT source archived with hash under `logs/roadmap/primitives-reference-01`.
Only observed detectable ground units outside the structure class trigger
sieging; target zone centers stay within native5tile range, and active transforms
are not interrupted. Deployed units use engine automatic fire; leave ground mode
when relevant targets disappear from10tile neighborhood.

Native fixture verifies two tank kills credited to the Liberator, a surviving
tank leaving the zone, one deployment/undeployment and zero errors. Debug setup
supplies the units but no resource/upgrades boost; this checks command execution,
not full-game or learned micro strength. Evidence:
`logs/roadmap/liberator-micro-fixture-01/verification.json`. Three regression tests
and the617test default suite pass (40optional skips). Full-game transfer remains
open; prior scripted Hard results precede this addition.
