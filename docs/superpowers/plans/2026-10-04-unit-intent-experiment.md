# Unit Intent Experiment Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline. Existing autonomous authorization overrides a routine handoff pause.

**Goal:** Test whether RL-selected unit intentions overcome affordability/queue barriers to Terran tech production and improve frozen Hard results.

**Architecture:** A separate archived source adds a TerranLearner subclass. RL chooses all existing macro actions at fixed five-second intervals. Unit choices remain pending until issued once or replaced at the next decision; automatic retries only test normal affordability, supply, tech and idle-producer conditions. Building, research, stance and worker/combat behavior remain existing atomic primitives.

**Tech Stack:** Existing NumPy/BurnySC2/PPO/Torch CPU helper and unittest; no downloads.

**Spec:** docs/superpowers/plans/2026-10-04-primitive-and-affordance-audit.md

## Global Constraints

- Keep production and retained checkpoint untouched; experiment under logs/audit/ppo-unit-intent-source.
- No scripted build order, unit mix, saving priorities or automatic prerequisite construction.
- Decisions exactly five game seconds apart; gamma=.99 matches the existing per-time discount. Compare to a five-second immediate-action control.
- Unit intent selection requires a ready producer and tech, but may lack resources/supply or have busy producers. Actual execution retains every original constraint.
- At most one unit command per chosen intent, including SCV; retries run after worker/combat micro.
- Wait, structures, research, attack/retreat and a different unit replace prior intent at the next decision. No unbounded lock.
- Observe ten pending-unit one-hots and pending age/5, alongside original live units/spatial features. Checkpoint schema and reward/interface label distinguish this arm.
- All jobs quiet wrapper, <=4 simultaneous games, 8 allowed CPUs, nice+10, numerical threads1, CPU learning.
- Reserve acceptance seed50000. Smoke/fixtures cannot establish strength.

## Review Focus

- Resource shortage or busy producer: selectable intent, no illegal command.
- Pending command becomes executable: issue once, with actual issued time in originating decision receipt.
- Cancellation/replacement: old intent cannot execute after a new policy choice.
- PPO transitions: fixed five-second cadence and next observations include pending state, terminal shaping retained.
- Migration: original input rows/parameters/moments/RNG exact, new input rows zero, cadence/gamma/interface changes explicit.

### Task 1: Unit intent executor and observation

Files: archived src/rl/intent_terran.py; tests/test_unit_intent.py; src/rl/train.py import only.

- [x] Write failing tests for selectable unaffordable/busy units, tech/producers still required; actual retries obey original legal mask, execute once, and record issuance; cancellation/replacement; pending observation and encoding.
- [x] Run focused unittest and confirm failures identify missing behavior.
- [x] Implement subclass and wire archived trainer; preserve production source.
- [x] Run full archived unittest suite and request existing independent reviewer.

### Task 2: Migration and runtime verification

- [x] Migrate retained0f3 checkpoint by feature name with zero new rows/moments, original outputs exact on recorded states; cadence5/gamma.99/explicit label. Matched immediate control changes cadence/gamma only.
- [x] Test supervised actual SC2 fixture: choose unaffordable unit, restore ordinary resources, observe one unit completion; busy producer waits; cancellation prevents issuance. Debug fixture excluded from learning.
- [x] Run/resume two VeryEasy smoke games per arm, audit trajectories and immutable frozen eval.

### Task 3: Bounded matched learning comparison

- [ ] Before launch, freeze both source hashes and initial checkpoints. Train40 Hard episodes per arm, four workers, same first scheduled seed30144 (CLI seed30000 plus144 prior attempts), two maps, all three races/five builds, unchanged reward/PPO settings. No extending failing arms.
- [ ] Evaluate greedy development banks20000/40000,30 games each. Joint14/13 effort gate remains, compare actual unit diversity and command completion as secondary diagnostics.
- [ ] Audit returns, masks, source/weights immutability, full schedules, failures. Infrastructure failure requires preserved receipt and full repeat from initial.
- [ ] Only a passing arm can proceed toward independent final70% frozen30-game bank50000 acceptance. No reliable-Hard claim before acceptance.

## Implementation and verification ledger

Task1 complete: four new tests fail before implementation (missing module), then pass; archived full85-test suite passes. Initial full suite failed five tests: four still targeted old training schema and one lacked copied plot config. Adapted only archived training-test imports and copied original config/tools. Production source unchanged. New module96lines; trainer import only.

Task2 complete: migration verifies17323 old states, max logit/value error2.22e-16, all old parameters/moments/RNG exact, new input rows zero. Source and contexts independently reviewed. Migration overwrite guard rejects rerun without changing inputs/receipt. Actual SC2 fixture covers unaffordable wait, busy wait, once-only issuance and cancellation, three Vikings complete. First fixture correctly hit supply limit; failed receipt preserved and fixture supply corrected. Six120-second smoke games per arm (train2/resume2/frozen2) allTie with zero failures,148episodes/attempts and684updates. Frozen checkpoints unchanged.144states per arm, return errors<=2.92e-16. Intent smoke39issued/17delayed/26cancelled; issuance alone is not completion.

Ruling: first pass persists unit choices only; structure/research/stance remain atomic. Evidence currently concerns unit affordability/queues, and this keeps the intervention bounded. Lack of automatically constructed prerequisites is deliberate and tested. The combined selection-mask/persistence intervention also has11additional observation features; matched cadence is controlled, but those components are not separately identified.

Task3 inputs frozen in each predeclared-run.json before launch; sources must remain unchanged during jobs. Keep primary and all archived evidence. No Astra consultation needed yet: concrete diagnostics and implementation have progressed.

Hard intent run completed under supervisor session3014. During the first four-game batch, five sampled two-second windows show whole-host CPU13.04–13.52%, owned CPU lower bound12.37–12.48%, aggregate RSS peak4.636GiB. All ten observed owned processes use CPUs24–31 and nice+10. GPU instantaneous10%,20.71W,40C. Receipt logs/audit/unit-intent-hard-resource-load.json. This is a live sample, not an overnight peak guarantee. Matched control completed under supervisor session76673; keep total concurrency<=4games.

## Intent Hard40 result

The full predeclared intent run completes0Victory/38Defeat/2Tie, zero game/learner failures. It yields6187decisions,2145unit-intent command issuances (362delayed) and958cancelled intentions,184episodes/attempts and788optimizer updates. Final/frozen checkpoint SHA256: `9bcba2c69dc4779182ebe6778b0deb8500e60c9455145ea5aee12db13b033971`. Observed type presence across40games includes36Marauder,16Tank,8Medivac,10Viking and2Raven games; all40have Marines. This confirms exercised production choices, not effective strategy or causal improvement. No untrained/trained greedy result is available yet.

`logs/audit/unit-intent-learning-audit.py ppo-unit-intent` verifies the full40seed/case schedule, source/behavior hashes, selected mask membership, recorded potential/combat rewards, terminal payoff/zero potential, finite optimizer state and discounted returns (maximum error9.44e-16). Existing independent reviewer reproduces the audit under the quiet wrapper and checks all ten optimizer boundaries/increments. Logged mask membership is not an independent reconstruction of physical legality; capability fixtures establish selected primitive conditions separately. Receipt: `logs/audit/ppo-unit-intent-learning-results.json`; actual source remains frozen.

Matched immediate-five-second Hard40 control has started from its untouched initial weights, with the same predeclared schedule, batches, objective and time discount. Run it to completion before attributing outcomes to the intervention. Frozen development banks20000/40000 and acceptance50000 remain unexecuted for these arms. Production and retained checkpoint remain unchanged.

## Matched control and credit audit

Control Hard40 completes0Victory/37Defeat/3Tie, zero failures,6156decisions,184episodes/attempts and792optimizer updates. Frozen SHA256: `94e9e2c5f902c3267467d7d9d4430a2241471c1f635af54479390d8de8e3c259`. Existing independent reviewer checks full case/source/checkpoint histories, all ten optimizer boundaries, terminal contract and discounted returns (maximum error1.30e-15). Control observes Marauders39,Tanks18,Medivacs6,Vikings7,Battlecruisers2,Ravens2 games. Neither zero-win arm demonstrates a strength difference, and their diverse sampled unit production does not show that persistence alone caused diversity. Receipt: `logs/audit/ppo-immediate-five-second-learning-results.json`.

A read-only host snapshot during control covers111threads in ten owned processes; all use CPUs24–31 and nice+10. Receipt: `logs/audit/immediate-five-second-thread-affinity.json`.

`logs/audit/unit-intent-credit-decomposition.json` separates actual discounted rewards. Potential shaping contributes exactly-.08 in every intent episode, all40have zero victory credit, and combat credit has min0/median.0339827/max.2600023. With completed trajectories, constant gamma and zero terminal potential, the potential terms telescope. They redistribute temporal credit without adding episode-level growth preference. This is intended potential shaping, not a numerical bug or demonstrated cause of failure. State-relative PPO targets still include the potential term. Independently reviewed.

The first intent frozen development bank20000 completes0Victory/30Defeat/0Tie, zero failures and immutable weights. Its40000bank is now running under session81809. Control bank20000 also completes0Victory/30Defeat/0Tie with zero failures. Its40000bank is now live under session7704, after the prior two workers terminate. Both gates are already mathematically unreachable on bank20000, but complete the predeclared comparison schedules before closing the arms. No learning extension or promotion; acceptance50000 untouched.

## Conditional Astra consultation

The user permitted an Astra ideas agent if material playing-strength progress stalled and root ran out of supported next ideas. Repeated failed strength arms now satisfy that condition despite engineering progress. A read-only Astra review found no new executor/likelihood bug and identified episode-level exploration/data/credit as its leading hypothesis. This is an advisory judgment, not proven causality. It recommends a frozen episode-coherent bias-perturbation pilot of the original retained policy/cadence before another PPO run: four fixed antithetic direction pairs, outcome-free calibration near5%changed greedy decisions, eight policies on two fresh predeclared training cases plus unperturbed controls (18games), genuine behavior-change/win/return variation criterion. Deterministic trajectories must not be placed into the categorical PPO updater. Controls losing makes winning-preservation evidence inconclusive. No pilot has started; finish current comparisons first.

First frozen comparison independently reconstructs every greedy choice on all actual visited states, full case/source provenance and checkpoint immutability: both arms0/30 on bank20000, both effort gates failed. Receipt `logs/audit/unit-intent-frozen20000-results.json`. Complete bank40000 for the declared comparison; no promotion or further training of either arm. Source, reward and parameter-search considerations from Astra remain advisory until a separately declared experiment produces evidence.
