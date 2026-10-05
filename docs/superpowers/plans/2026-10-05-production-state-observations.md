# Production-state observation experiment

Goal: determine whether missing fully observable production state supplies useful planning information, then test learned play only if that information gate passes. Reliable Hard strength remains the final objective; prediction quality is not strength acceptance.

Evidence: main5460features include identity/grid and macro counts, idle Barracks/townhalls and aggregate ready Tech Labs, but not explicit factory/starport queues, construction progress or per-producer ready-lab attachment. The failed bias search produced valid updates but regressed its Medium monitor. Authorized read-only Astra recommends isolating sensing before temporal credit or stance semantics. These are hypotheses, not proven causes.

## Observational probe

Create an isolated frozen-source archive. Record six retained-policy Medium cases, exactly the prior complete monitor schedule86000–86005, to verify instrumentation parity. Cases are reused for trace comparison and information measurement, not fresh strength evidence. Retained0f3checkpoint, one-second cadence,27actions, original micro/masks/commands/objective remain unchanged. Add a nested public production telemetry field to snapshots, ignored by the old encoder. No extra commands or engine queries; no debug resources or hidden opponent data.

Define35numeric features:

- For ground Command Centers/other townhalls, Barracks, Factories and Starports, matching the actual executor's producer groups: unfinished count, ready count, ready-idle count, unit-training queue count, maximum unit-order progress, maximum unfinished building progress, unit-queue-present indicator. Counts indicate presence for unfinished progress; queue indicator disambiguates absent queues. Progress maxima are fractions, not estimates of remaining seconds.
- For each of Barracks/Factory/Starport: ready producer count with attached ready Tech Lab, and ready-idle count with attached ready Tech Lab. Resolve attachment tags using the same public ready-lab set as the executor.
- Nominal pending supply capacity from public pending Depot/Command Center counts times protocol-provided supply. Distinguish pending from currently available supply; do not imply every unfinished order completes.

Classify unit-training orders using matching public unit creation-ability IDs, excluding move/research/add-on orders. Reactor simultaneous training is counted as orders, not inferred goals. Scale producer/queue counts by8, progress/presence by1, pending capacity by64; clip normalized added inputs to[0,2]. No target counts or preferred units.

Verify six full schedules, hashes, no failures and unchanged checkpoint. Strip only the telemetry field and require each decision's original snapshot, legal mask, action, execution and reward fields to match the uninstrumented baseline. Outcome/duration parity alone is insufficient. Preserve any mismatch; do not silently substitute cases or call the probe transparent.

## Information gate

Only after parity passes, use leave-one-whole-game-out prediction (six folds). Predict next-decision ready/idle producer presence, ready-idle attached-lab presence, and production-related legal-mask bits. Features are the full old observation plus current chosen-action one-hot in both predictors; the sensory predictor additionally receives the35current public telemetry features. No next-state input or outcome labels as features.

Use fixed multi-output ridge regression with penalty10, training-only centering/scaling and zero-variance column removal, separate intercept. Clip predictions to[0,1] for Brier error. Binary thresholds equal training label prevalence for balanced error comparison, identically for both predictors. No hyperparameter/difficulty/case selection based on held-out scores.

Exclude fold/labels lacking at least20positive and20negative training samples or held-out variation. Report support, Brier/balanced errors and per-producer/mask results, including excluded and unexposed conditions. Gate requires>=10percent relative reduction in aggregate held-out Brier error, lower aggregate Brier on>=4of6whole-game folds, and>=2labels improving balanced accuracy by>=3percentage points. This is diagnostic support for these inputs, not proof of causal playing improvement or sufficient overall sensing. Stop this sensory route if support is insufficient or the gate fails.

## Conditional matched learning

Do not launch learning until the information gate passes and a concrete comparison schedule is separately frozen. Append35input rows initialized to zero, preserving all retained outputs/old parameters/moments/RNG before training. Use the same verified PPO algorithm/context in both arms, same fresh Medium cases and budgets. Only observation inputs differ; no changes to reward, cadence, stance masks, persistence or micro. Actual full masks/returns/context/update audits and separate frozen checks required.

Progress requires frozen sensory-arm improvement over both unchanged parent and matched old-observation control; predictor gains, more advanced units, training returns and issuance counts are insufficient. Do not promote from six reused probe games. Original14/13development effort gate and reserved70percent30game Hard bank50000 remain unchanged.

If sensing fails its comparison, defer further exposure/architecture additions and investigate time-normalized bootstrapped advantage estimation with independently validated critic. Do not combine hypotheses.

Resource constraints: no installs/sudo, eight CPUs/nice+10/BLAS1/softwareGL/CPU-only, at most four supervised game workers, wall180/game1200seconds, preserve interruption/failure receipts. No probe has started at predeclaration.

## Verified probe and information ledger

Four observation tests fail before implementation, then pass. First synthetic fixture omitted Command Center protocol data; corrected fixture only and preserved failed output. Archived full85tests pass. Independent reviewer checks generic-remapped creation/order abilities, same executor lab-tag semantics, cached-only reads and spawn patch; no material defect. Six observational games finish with zero failures, immutable0f3weights and frozen sources. Full3183decision traces match baseline after removing only production_state, including snapshot/mask/choice/execution/reward fields, outcomes and exact durations. Independent parity reconstruction passes. `logs/production-state-probe/parity-audit.json`.

Observed coverage:1652townhall/2134Barracks/817Factory queue states,1260unfinishedBarracks/200unfinishedFactory/171unfinishedtownhall states,1511attachedreadyFactoryLab/153BarracksLab states and1672pending-supply states. Starports unexposed. This is logged exposure and consistency, not independent raw-order reconstruction.

Five predictor tests pass for signal/sign-independent fit, class-balanced accuracy, training-only normalization/constant-column removal, whole-game holdout and current-features/next-label alignment. No hyperparameter selection. Information gate passes narrowly: weightedBrier .2375390161673737to.2127471894668375,10.4369493percent reduction;5of6folds improve (one only5.76e-6). Balanced-accuracy gains exceed3points for BarracksIdle3.97,FactoryIdle15.51,FactoryIdleLab14.40 andBarracksIdleLab6.07points; latter onlytwoeligiblefolds.78fold/label exclusions explicitly reported, including absentStarport conditions.

Independent reviewer reconstructs training-only means/scales/columns, saved ridge models/predictions, all exclusions and metrics; maximum normal-equation residual1.73e-11. No held-out normalization leakage or outcome labels. `logs/production-state-probe/information/results.json`. Narrow diagnostic support permits the separately declared matched observation comparison; no playing-strength claim or production default change.
