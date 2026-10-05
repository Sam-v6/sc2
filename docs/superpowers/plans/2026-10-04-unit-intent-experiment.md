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

- [ ] Write failing tests for selectable unaffordable/busy units, tech/producers still required; actual retries obey original legal mask, execute once, and record issuance; cancellation/replacement; pending observation and encoding.
- [ ] Run focused unittest and confirm failures identify missing behavior.
- [ ] Implement subclass and wire archived trainer; preserve production source.
- [ ] Run full archived unittest suite and request existing independent reviewer.

### Task 2: Migration and runtime verification

- [ ] Migrate retained0f3 checkpoint by feature name with zero new rows/moments, original outputs exact on recorded states; cadence5/gamma.99/explicit label. Matched immediate control changes cadence/gamma only.
- [ ] Test supervised actual SC2 fixture: choose unaffordable unit, restore ordinary resources, observe one unit completion; busy producer waits; cancellation prevents issuance. Debug fixture excluded from learning.
- [ ] Run/resume two VeryEasy smoke games per arm, audit trajectories and immutable frozen eval.

### Task 3: Bounded matched learning comparison

- [ ] Before launch, freeze both source hashes and initial checkpoints. Train40 Hard episodes per arm, four workers, same first scheduled seed30144 (CLI seed30000 plus144 prior attempts), two maps, all three races/five builds, unchanged reward/PPO settings. No extending failing arms.
- [ ] Evaluate greedy development banks20000/40000,30 games each. Joint14/13 effort gate remains, compare actual unit diversity and command completion as secondary diagnostics.
- [ ] Audit returns, masks, source/weights immutability, full schedules, failures. Infrastructure failure requires preserved receipt and full repeat from initial.
- [ ] Only a passing arm can proceed toward independent final70% frozen30-game bank50000 acceptance. No reliable-Hard claim before acceptance.

## Implementation and verification ledger

Task1 complete: four new tests fail before implementation (missing module), then pass; archived full85-test suite passes. Initial full suite failed five tests: four still targeted old training schema and one lacked copied plot config. Adapted only archived training-test imports and copied original config/tools. Production source unchanged. New module99lines; trainer import only.

Task2 complete: migration verifies17323 old states, max logit/value error2.22e-16, all old parameters/moments/RNG exact, new input rows zero. Source and contexts independently reviewed. Migration overwrite guard rejects rerun without changing inputs/receipt. Actual SC2 fixture covers unaffordable wait, busy wait, once-only issuance and cancellation, three Vikings complete. First fixture correctly hit supply limit; failed receipt preserved and fixture supply corrected. Six120-second smoke games per arm (train2/resume2/frozen2) allTie with zero failures,148episodes/attempts and684updates. Frozen checkpoints unchanged.144states per arm, return errors<=2.92e-16. Intent smoke39issued/17delayed/26cancelled; issuance alone is not completion.

Ruling: first pass persists unit choices only; structure/research/stance remain atomic. Evidence currently concerns unit affordability/queues, and this keeps the intervention bounded. Lack of automatically constructed prerequisites is deliberate and tested. The combined selection-mask/persistence intervention also has11additional observation features; matched cadence is controlled, but those components are not separately identified.

Task3 inputs frozen in each predeclared-run.json before launch; sources must remain unchanged during jobs. Keep primary and all archived evidence. No Astra consultation needed yet: concrete diagnostics and implementation have progressed.
