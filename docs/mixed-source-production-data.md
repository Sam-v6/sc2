# Verified data for the mixed-source production experiment

Eight existing native human games now have dense current observations and
production timing labels. Professional choice examples are separately prepared
at their original issue states. No model fitting, prediction, bot competition
or RL ran during this preparation. This is data readiness for a bounded transfer
experiment, not evidence of learned game strength.

## Native timing

`logs/roadmap/dense-timing-cohort-01/` freezes five Mez teaching games, Lyra's
50925 for calibration, and Huski 51960 / Rom 51482 for evaluation. Calibration and
evaluation are reused diagnostics from different named players; they are not
fresh acceptance. The original roles apply to both views, human losses remain,
and reserved 51886 is untouched. Rom's previously verified dense reconstruction
is reused; seven other replays are reconstructed sequentially to terminal results.
The seven new jobs take 1,068.45 combined wall seconds and sample 23.2% peak host CPU.
GPU remains disabled. No assets or replays are downloaded.

All eight sources supply 102,680 consecutive single-loop observations and 2,338
retained current states at 44-loop cadence. Complete intervals cover 102,520 of
102,672 elapsed loops (99.85%); unsupported game-end tails remain explicit. Native
state L labels original human issuance in (L, L+44], consistently with pre-command
alignment. Engine command-manager repetitions are explicitly excluded from this
human timing target. They remain in the raw archives. Current gate observations
have human command history removed; future event keys appear only in labels.

`logs/roadmap/native-production-timing-02/` checks native ability, target, queue,
own actors and mutual uniqueness against every original human SCmdEvent. Reader
data pack 70154 is older than engine 75689; reader names alone do not establish
quiet intervals. Extra nonproduction matching requires native button-name or
basic-command family identity and the original command index. For example,
Attack corresponds to native Attack Attack; HoldPosition to HoldPosition Hold.
KD8Charge's incorrect reader name remains unresolved. Unknown flags, unmatched
commands and unsupported tails stay censored. Source observations and the broad
human corpus are unchanged.

| Role | Current states | Production confirmed | Waiting confirmed | Unknown |
|---|---:|---:|---:|---:|
| Teaching: Mez, five games |1,674|467|1,002|205|
| Calibration: Lyra, reused |300|97|173|30|
| Evaluation: Huski/Rom, reused |364|95|234|35|

Teaching labels retain 12.2% uncertainty, and only one named teaching player is
represented. Among resolved windows, 31.8% are positive; across all windows the
possible positive fraction is 27.9–40.1%. Do not present the selected fraction as
the true production rate. Report censored counts and unknown-window predictions
alongside calibration, phase coverage and quiet-window false positives. The much
larger verified negative set and dense observation coverage support testing the
declared transfer hypothesis once; they do not remove these limitations.

The independent verifier redecodes all original events and checks exact native
proof positions, ownership, targets, queues, names/indices, catalogue unit and
upgrade references, numeric identity references, every current observation and
every timing label. It separately checks complete interval coverage and current
enemy visibility. An initial verifier lacked the catalogue-upgrade naming path
for CycloneLockOnDamageUpgrade; that source-backed path was added before it passed.
No labels were changed to accommodate the failure. Source snapshots and bindings
are retained. Historical memory updates are not independently reconstructed at
every loop by this timing verifier.

## Professional production choice

`logs/roadmap/professional-production-choice-01/` contains 1,267 teaching and 289
reused diagnostic production events from the verified professional command
cohort. Each event appears once, at its own current pre-effect issue-loop state.
No future-window duplication or future actor/target input is introduced. Original
command arguments remain labels; this experiment trains conditional ability
choice, not full raw argument execution. The professional cohort includes
provenance-backed manager repetitions, so its decision definition is not identical
to the original-human SCmdEvent timing target; report that transfer assumption.

The independent verifier preserves every original observation except clearing
causal human history, checks exact event and ability/argument identity, verifies
1,556 distinct game/event keys and source bindings, and confirms declared roles.
Six professional teaching games still include two human losses; source diversity
and reserved games are unchanged.

Two small reusable helpers implement native interval boundaries and strict
catalogue-backed nonproduction identity. Their ten regression tests were written
before implementation. Full suite: 570 tests, 32 optional skips; Ruff and whitespace
checks pass. Next implement and run the single frozen supervised experiment in
[the experiment plan](mixed-source-production-experiment.md); no architecture,
epoch or native threshold sweeps after a failed gate. Native supply/scout transfer
and actual learned production effects remain required before any competence claim.
