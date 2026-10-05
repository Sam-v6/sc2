# Bounded action-bias parameter-search learning

Goal: test whether coherent reward-driven policy changes improve Easy play after repeated categorical PPO regressions. This does not establish reliable Hard strength or observation sufficiency.

User-authorized Astra consultation recommends a different learning mechanism. The prior frozen pilot stopped inconclusive because both controls lost, without testing perturbations. Parameter search can use paired return differences even when the incumbent loses.

Use an isolated archive and separately labeled `bias-es` checkpoint algorithm. Start with retained richer-policy weights, unchanged 5460 live features, 27 actions, one-second cadence, reward, masks and scripted execution/micro. Freeze body/output weights/value arrays. Optimize only 27 output biases. Do not feed deterministic trajectories to PPO or claim its optimizer state was updated. Zero optimizer arrays on explicit migration; preserve RNG and historical PPO counters as provenance, with separate ES generation/game counters.

Predeclare independently of outcomes:

- Four generations, two standard-normal zero-mean/RMS-one directions and their negatives per generation; direction seed71333.
- Reuse outcome-free scale0.03118564886972308; perturbation held constant whole episode, masked argmax.
- Eight fresh training cases, two shared by all four candidates and incumbent in each generation: five policies times two cases, ten games/generation,40 total. Case seeds83000–83007; rotate Terran/Protoss/Zerg, buildsRush/Timing/Power/Macro/Air, mapsSimple64/TritonLE to cover all races/builds/maps. No result-based replacements.
- Six separate Easy monitoring cases84000–84005, two per race and three per map, builds cycle. Identical before/after schedules;12monitoring games maximum. If initial5/6 or6/6, stop Easy before training and require a separately predeclared Medium arm.
- Two-direction ES estimate weights directions by their mean antithetic discounted-return difference. Exact ties contribute zero. Normalize nonzero update; cap movement to<=1percent additional greedy-choice disagreement with incumbent on all33556fixed recorded calibration states. Scale cap and directions cannot use monitor outcomes. Apply declared estimate, never select a single winning candidate as incumbent.
- Ordinary games, no debug,1200game/180wall seconds, quiet wrapper eight CPUs/nice+10/BLAS1/CPU-only,<=4 games. Preserve source, policies, schedules, replay/action/result receipts and all failures. Infrastructure failure closes the arm pending a fully declared repeat, not selective retry.

Implementation checks:

1. Synthetic sign, antithetic cancellation/exact tie and behavior-cap checks; migration exact non-bias arrays/metadata and algorithm isolation. Source frozen before games.
2. Supervised runner reuses owned process groups, bounded batch and interruption receipt harvesting. Immutable policies during each generation's games.
3. Actual masked greedy reconstruction, returns, cases/replays/source/checkpoint hashes, no PPO calls, exact ES update reconstruction.

Progress interpretation:

- Mechanism: at least two generations with nonzero paired return differences and meaningful actual deviations (>=5changed executed non-wait decisions and>=1percent non-forced decision changes for a candidate). This proves usable search information only.
- Learning: final monitoring wins increase by>=2 and mean existing-objective discounted return does not decrease. This permits a larger separately checked arm; it is not statistical acceptance.
- Stop without extension/promotion if no useful separation, learning gate fails, or deviations are primarily pathological waiting/stance cycling. Report executed production and stance changes to interpret behavior, with no retrospective numerical stop threshold.
- Final Hard development14/13 effort gate and reserved70percent30game bank50000 unchanged.27global biases cannot learn new state-dependent representations; negative evidence directs next work toward temporal credit and production-state observability rather than more PPO temperature/LR sweeps.

Status: predeclared plan only. No learning games or ES implementation yet.

Pre-launch provenance correction: seeds81000–81002 already appear in older VeryEasy smoke receipts. Without inspecting outcomes, changed the entire training/monitor seed banks to fresh83000–83007/84000–84005; receipt search has no matches. Cases/difficulty/schedules otherwise unchanged. No games or frozen inputs existed when corrected. Archived full85tests pass; four new tests were red before implementation then green. Batch interruption regressions pass.

Pre-game review identifies a feasibility ceiling: initial5/6 also cannot improve by two wins. Corrected stop condition before inputs/games to any initial win count+2 exceeding monitor case count (5or6wins), with a focused regression. Otherwise independent review finds no material ES/sign/cap/algorithm/supervision defect.

## Easy ceiling closure and Medium predeclaration

Initial Easy monitor wins6/6, all races/both maps/five builds, zero failures. Actual audit reconstructs all greedy choices and immutable source/model/results. Per ceiling rule no training or ES update occurs. This is successful frozen Easy play, not newly learned strength. Artifact `logs/bias-search-easy/learning-audit.json`. Four-game live hostCPU12.675–13.608percent, owned lower bound9.351–12.487percent, GPU10percent20.20W39C, all sampled owned processes affinity24–31/nice10; receipt `logs/audit/bias-search-resource-load.json`.

Predeclare an otherwise identical Medium arm before any new games: `logs/bias-search-medium/source`, original retained checkpoint, same ES migration/updates/directions/cap/calibration,40training games maximum plus12monitor games. Change difficulty toMedium and whole seed banks to fresh85000–85007training/86000–86005monitor; receipt search has no matches. Cases rotate exactly as Easy; no case selection from outcomes. Initial5/6or6/6 invokes the same insufficient-improvement-room stop, requiring another separately declared difficulty. Same mechanism/learning gates and finalHard acceptance unchanged. Sources/inputs freeze before launch.

## Verified implementation ledger

Isolated `src/rl/bias_search.py` defines bias-es loading/migration, mirrored update and masked incumbent-relative1percent behavior cap. Archived policy loader explicitly recognizes bias-es; categorical trajectory ingestion rejects. Four algorithm tests fail before implementation and pass after; fifth checks5/6and6/6ceiling impossibility. Archived full85test suite passes before the fifth addition; focused5tests and bounded waiting/submission interruption regressions pass afterward. Main production code unchanged.

Independent input audit confirms initialSHA256 `e8fd616e38e0c528f83e8febfa7e8dfb832f989e8ed9dd77f77b131238b453ee`, exact6network arrays/RNG/reward/cadence, zeroPPOoptimizer/rollout/update counters, historical provenance, all47source files, all33556calibration states/hashes, seeded directions and schedules. Independent reviewer reproduces Easy closure and Medium inputs; only source differences are difficulty/banks/stop wording. Medium monitor run live under supervisor80476. Do not modify frozen sources or inputs during games.
