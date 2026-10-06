# Terran primitives implementation and native development checks

The controller is explicitly scripted. No professional-imitation fit or RL runs
in this phase. Its role is to prove execution before reconnecting human decisions
and eventually RL. It does not replace the broad raw-command learning roadmap.

`src/bots/terran_primitives.py` contains worker assignment, target compatibility,
cooldown movement, tank transformations, order deduplication and destination
arrival checks. `scripted_targets` is the separately named baseline strategy.
`src/bots/primitive_terran.py` connects these rules to native SC2: protected
builders, interrupted construction, repairs, worker/Marine/Tank/Medivac
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
- The latest full suite passes 440 tests with 32 optional skips. The opt-in native
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

## Active next check

`logs/roadmap/primitives-native-02/panel` freezes the repaired source and the same
six Hard development jobs: AcropolisLE, Rush/Macro per race, seeds 818101–818106,
step eight, 1,200 game seconds, 300 wall seconds per game, sequential CPU-only
execution, and cancellation after three sampled whole-host readings above
80 percent. No source changes during the panel.

After it finishes, run
`PYTHONPATH=. .venv/bin/python logs/roadmap/verify_primitives_native_panel_02.py`.
The verifier checks replay outcomes and tracker production, reconstructs action
failure counts, and checks enemy visibility-grid/weapon compatibility on sampled
macro frames. Six development games do not satisfy the 30-game acceptance gate.
Diagnose failures, verify remaining primitives, then freeze the all-race Hard
acceptance panel. Only afterward resume professional imitation and, following
useful native imitation, RL and learned micro transfer.
