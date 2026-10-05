# Bounded action-bias parameter-search learning

Goal: test whether coherent reward-driven policy changes improve Easy play after repeated categorical PPO regressions. This does not establish reliable Hard strength or observation sufficiency.

User-authorized Astra consultation recommends a different learning mechanism. The prior frozen pilot stopped inconclusive because both controls lost, without testing perturbations. Parameter search can use paired return differences even when the incumbent loses.

Use an isolated archive and separately labeled `bias-es` checkpoint algorithm. Start with retained richer-policy weights, unchanged 5460 live features, 27 actions, one-second cadence, reward, masks and scripted execution/micro. Freeze body/output weights/value arrays. Optimize only 27 output biases. Do not feed deterministic trajectories to PPO or claim its optimizer state was updated. Zero optimizer arrays on explicit migration; preserve RNG and historical PPO counters as provenance, with separate ES generation/game counters.

Predeclare independently of outcomes:

- Four generations, two standard-normal zero-mean/RMS-one directions and their negatives per generation; direction seed71333.
- Reuse outcome-free scale0.03118564886972308; perturbation held constant whole episode, masked argmax.
- Eight fresh training cases, two shared by all four candidates and incumbent in each generation: five policies times two cases, ten games/generation,40 total. Case seeds81000–81007; rotate Terran/Protoss/Zerg, buildsRush/Timing/Power/Macro/Air, mapsSimple64/TritonLE to cover all races/builds/maps. No result-based replacements.
- Six separate Easy monitoring cases82000–82005, two per race and three per map, builds cycle. Identical before/after schedules;12monitoring games maximum. If initial6/6, stop Easy before training and require a separately predeclared Medium arm.
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
