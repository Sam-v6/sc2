# Human inventory targets: matched native result

This experiment is closed as failed against its original mechanism gate.
The verified lookup chooses one professional human's complete future inventory
from game time, current workers and total town halls, using public selected race.
The executor requests only positive target-minus-current deficits, subtracts
already queued work, retires unissued satisfied/replaced intents and preserves
accepted work. It has no recent production-rate quota or scripted building caps.

Tests cover public Random versus hidden actual race, whole source vectors and
holds, unsupported observations, intent retirement, accepted work, replacement
of lost stock, remembered foundations and integration without count-model calls.
505 tests pass, 32 skipped; named-file Ruff passes. Runtime selections exactly
match all 281 saved offline native forecasts before this comparison ran.

The frozen pair uses AcropolisLE, Zerg VeryEasy Rush, seed816201, 600 game seconds,
240 wall seconds per arm, identical scout/mining/combat assistance and human
precedence, two CPU threads and the 80% whole-host guard. No fitting or RL.

| Metric | Cadence control C | Inventory lookup I | Declared gate |
| --- | --- | --- | --- |
| Result | Tie | Tie | Victory needed for competence progress |
| Completed Barracks/Factory/Starport | 3 | 5 | More: passes |
| Military births | 33 | 41 | At least 50% more: fails |
| Final minerals | 6,715 | 3,355 | At least 50% lower: passes |
| Living SCVs | 74 | 52 | At least 90% retained: fails |
| Sampled supply-blocked seconds | 14.29 | 70.36 | No increase: fails |
| Native wall seconds | 48.36 | 41.66 | Within supervision limit |
| Sampled whole-host CPU peak | 6.9% | 5.0% | Below ceiling |

Independent verification reconstructs each held source/target, observed stock,
future queue, full intent lifecycle including retirement/expiry/acknowledgements,
command attribution and native births. It independently reconstructs final living
SCVs and completed production buildings from tracker events; workers temporarily
absent from raw observations are included. Raw visible-worker totals alone would
understate the totals (70/49). All intervention selections are within the frozen
support limits, which does not establish strategy suitability or competence.

The intervention adds Terran production diversity, Tanks, Medivacs, Banshees and
human upgrade requests. But lower worker growth and supply blocking remain real.
It selects game523 repeatedly after 90 seconds: future worker targets 18 at90s,
19 at135s, 26 at270s and 42 at450s. Matching a struggling bot's worker count can
keep it near a slower economic trajectory. This is a causal hypothesis; it is
not a proven description of why the human chose that build.

32 forecast observations are supply-blocked with food-using production demand;
20 have no additional Depot deficit, because their held inventory already has
the requested Depot stock. Other blocked frames request a Depot but cannot submit
it. Aggregate native diagnostics include 48 Barracks placement blocks. Failed
placement details were not retained per request, so exact physical causes need
fresh instrumentation before repair. A replay-only placement probe rejects sites
across all tested owned bases. A control query at loop0 for a Depot site that
succeeded in the live game returns generic ActionResult Error (code3). These
replay-mode queries therefore cannot diagnose live build-space availability;
use instrumented live requests instead.

Do not promote this controller, weaken the gates, or restart RL. Preserve the
failed pair and its bound source snapshot in `human-inventory-native-01`.
Next establish the precise remaining placement/execution failures and identify
human examples that cover the demonstrated economic/supply recovery gap.
Broad human command imitation, learned micro and learned Hard/higher wins remain
required by the full roadmap.
