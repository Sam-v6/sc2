# Human inventory labels and failed first fit

Inventory labels now describe living owned units at a future instant, rather than
new production events. Canonical modes include lowered Depots, flying buildings,
sieged tanks, Vikings, burrowed mines and Liberator modes. The native catalogue's
unit_alias chains provide these mappings; HellionTank/Hellion is an explicit
reversible-mode exception. CommandCenter is total town halls, while Orbital and
Planetary heads separately count paid conversions. Foundations count immediately.

Current stock includes deduplicated owned memory. Ignoring that memory initially
under-counted workers; the first preparation is preserved and was not fitted.
Preparation03 and independent event-delta/prefix-sum verifiers reconstruct all
6354future labels and all imported current-stock baseline vectors. Labels use
tracker events strictly before the query loop. Current tracker and SDK stocks
agree6257/6354rows; all97remaining rows match an event prefix within the same loop.
This identifies an intra-frame phase ambiguity, not exact global parity. It remains
a disclosed limitation. Future information is labels only; original current-state
features, game split and reserved games remain untouched.

The one frozen128-tree/leaf4/seed8160/two-thread fit completed in15.953seconds.
Independent recomputation verifies all saved predictions and equal-game metrics:

| Development mean absolute error | Current-inventory persistence | Inventory model |
|---|---|---|
| All52families | 0.22650 | 0.22615 |
| Workers | 3.25896 | 1.77279 |
| Production buildings/addons | 0.14578 | 0.25180 |
| Other buildings | 0.16185 | 0.22189 |
| Military | 0.37891 | 0.36096 |

The production-building gate fails. Rounding to integer inventory does not fix it:
production MAE remains0.21918. The tiny overall gain is insufficient to establish
capacity planning. No native promotion, extra fit or RL. The initial wrapper
returned None to a supervisor expecting a result dictionary and failed after the
checkpoint/report were saved. Its traceback is preserved; independent verification
used those artifacts without refitting. Fit-thread CPU peak was11.6%; outer watcher
samples were lost with that wrapper failure, so there is no confirmed whole-run
supervision receipt. Sources/predictions/errors are preserved under
`logs/roadmap/human-inventory-targets-03`.

Original replay metadata also verifies public selected opponent races: teaching
has twoTerran, fourZerg and fiveProtoss games; development has oneZerg and twoProtoss.
Teaching Terran coverage exists; human development Terran coverage is absent. Use
SelectedRace (the public lobby choice), never hidden AssignedRace, for any new
context. Static imported game_info lacks player info; this field needs explicit
source-to-native parity if introduced.

Astra's read-only follow-up recommends one source-backed goal retrieval experiment:
select an actual human future inventory by economic stage, hold its entire vector,
and measure capacity recovery in native play. This is a separate transfer diagnostic,
not a revised passing gate for the failed regressor. It must trace the source
example and declare the assumption that similar economic stage supports the goal.
Scouting also needs transfer: the verified scripted baseline protects an SCV scout,
but the current human-production assistance omits it and sees no enemies until
roughly eight minutes in the examined game. Repair that primitive before comparing
retrieval with the cadence control, with identical assistance in both arms.
The broad human command/micro/RL/Hard/higher-difficulty roadmap remains incomplete.
