# Fresh Adam clocks for appended production inputs

The closed offline replay reproduced both original first updates exactly. Giving
only the appended35input rows a fresh Adam clock reduced excess probe policy KL
77.755%; blocking their critic gradients alone failed. Test that specific clock
correction in games. This does not assume it caused the earlier gameplay collapse.

## Inputs and implementation checks

Create a separate `logs/ppo-production-fresh-adam/source` archive from the closed
production-observation source. Preserve5495features,27actions, shared64hidden
units, critic gradients, reward/gamma/cadence, masks, primitives, all old network
arrays and Adam moments, RNG and counters. Start from the exact sensory initial
3232e40ff4a3ee3b04c2d6f45af59f8ca53a76e8d6beb0458bab5c5fe4af6eaf,
whose global optimizer age is676. Never use the diagnostic or smoke-trained weights.

Persist explicit metadata for this appended block: old-prefix5460 and birth
update676. Restore old parameter clocks from global updates, and appended clocks
from updates minus birth. Only split the first-layer parameter during optimization;
save the same six network/moment arrays. Create an explicitly recorded initial
migration that adds only this metadata to the original3232checkpoint; independently
verify every network/moment array, old metadata field and RNG unchanged, and
record the migrated file's new hash. Preserve the birth metadata through
save/load/resume. Reject missing or inconsistent birth metadata for this experiment
rather than silently reverting to an inherited clock. Main code/checkpoint
semantics remain unchanged.

Before games, demonstrate red-to-green tests for metadata persistence, fresh age,
old moment preservation, and the same resumed next update versus uninterrupted
updates on a small synthetic fixture. Reuse the fixed saved first batch for inference and independently compare
the corrected update against offline B arrays within absolute/relative1e-10.
This separately bounded full-batch implementation check uses at most one64-minibatch
update, plus the small focused resume fixture; no retuning or state selection.
Freeze source/input hashes and obtain independent review before actual runs.

Use disposable cloned inputs for train2/resume2/frozen2 VeryEasy smoke games,
120game/180wall seconds. Verify real helpers, birth metadata and counters,
nonzero exposed new-row gradients, and unchanged frozen bytes. Smoke outcomes
do not determine strength. The actual continuation starts untouched metadata-migrated initial bytes.

## Fixed game budget and comparisons

Train exactly40Medium games on the original matched schedule88144–88183,
rotating races/builds/maps as in the closed production-input experiment. Use four
workers and the same four-game collection/update grouping and horizons. Audit
the firstfourtrajectories for exact original trace parity and the first promotion
against offline B; stop on mismatch before interpreting later wins.

Then freeze the40game snapshot and evaluate exactly30Medium cases89000–89029,
ten per race, both maps and all five builds. Reuse the complete archived parent,
old-input control and inherited-clock sensory evaluations as named development
comparisons; they won22/30,21/30 and6/30, respectively. These are reused
development cases, not a fresh final acceptance bank.

Pass only with at least25/30wins (at least three above both parent and control),
mean discounted return at least their .4636294490/.4394904950, zero failures,
complete checkpoint/RNG/reward audits, and unchanged frozen bytes. No extension
or extra seeds if it fails. Regardless of outcome, retain sources, inputs,
receipts, full action logs and checkpoints, and render a matched replay if a
material gameplay difference needs inspection.

Only after that gate passes, run the two existing30caseHard development banks
20000and40000, requiring at least14/30and13/30. Do not use final acceptance
bank50000 or promote a model on Medium results. Reliable all-race Hard remains
the original unmet target.

## Limits

Six smoke games plus40training and30evaluation games; at most60conditional
Hard games after the Medium gate. No reward, learning-rate, temperature,
critic pathway, temporal-credit or primitive changes. CPU-only existing sibling
Torch, absolute non-resolved interpreter/Python-B, low_load eightCPUs/nice10,
BLAS/Torch1thread, at most four total SC2 engines. Sample active host load and
keep it below the user's40% whole-machine CPU preference. No sudo/downloads.

## Implementation and first actual batch

The isolated source passes93tests plus two focused Torch checks. Tests first
failed for missing metadata/optimizer restoration and then passed; two additional
corruption tests protect worker context and helper promotion. Independent review
caught and verified that promotion guard fix. All source files are frozen under
`logs/ppo-production-fresh-adam/source-manifest.json`; the original freeze is
retained, and the refreeze changes only the guard and its tests. No repeated
full-batch optimizer check was needed: updater/inference sources remain unchanged.

The metadata-only migration has hash
0d878a28e8f84abddef10f068163354c5bcd6fefc03f46b65aeebda04897dc31.
All numeric arrays and old metadata fields are exact. One64-minibatch real-helper
check reproduces all18offline-Bnetwork/moment arrays bitwise, updates740 and
exact RNG. Six disposable train/resume/frozen smoke games complete without
failures:224decisions per phase, updates680/684/684, final episodes/attempts148,
birth676 preserved, exposed new-row moments nonzero, frozen bytes unchanged.
Setup path/import failures and the earlier missing-initial test output are
preserved separately; they are not successful checks or gameplay evidence.

The actual continuation starts untouched migrated initial bytes. Its firstfour
Medium cases finish1Victory/3Defeats with zero failures. All3898decision traces
match the original games byte for byte. The actual promoted checkpoint matches
the corrected offline update exactly, including all18arrays, counters, RNG and
the whole checkpoint hash885f7a498dfc40ea4b16dfc9d636aa147eb0e21fb28ce7d622458c64ad66fbcb.
The first-batch gate therefore passes before the remaining36training games.
Splitting the command at this gate preserves the original four-game update
grouping, episode schedule, seed draws and settings.

The active four-engine host sample measures13.248–13.827% whole-machine CPU,
roughly12.4–12.5% owned CPU; all owned processes use24–31affinity/nice10.
GPU is13%/21.54W/40C; the learner uses CPU only. Resource receipt:
`logs/audit/production-fresh-adam-learning-resource-load.json`.

## Completed result: strength gate failed

All40training and30frozen Medium games completed without failures. Training
finished4Victories/30Defeats/6Ties across34124decisions. Frozen evaluation finished
7Victories/23Defeats across19941decisions, with mean discounted return .1143448847.
The parent won22/30, control21/30 and original sensory6/30 on these same development
cases. All four predeclared improvement checks fail. This arm is closed: no Hard
games, extension or promotion. The retained main policy remains unchanged.

Complete recorded-choice, reward, RNG and checkpoint-chain audit passed, followed
by independent verification of all70receipts and the frozen evaluation. Evidence:
`logs/ppo-production-fresh-adam/learning-audit.json` and
`logs/audit/production-fresh-adam-complete-independent-review.json`.
Final checkpoint SHA256:
15b28a130e6b65132e403a9f4ed348667f65924004efd782528016b066496506.

The previously selected89011Zerg/Macro/Simple64 case remains a defeat, now at
826.43game seconds. It produces up to31army units but never chooses SCV production;
parent and control won this case. Its actual replay exports successfully to
`logs/replay-proof/production-fresh-adam-medium-zerg-regression.mp4`:
843H264frames,960x720,4fps,210.75video seconds, full826.79game seconds, no frame cap.
ffprobe and a middle-game still verify usable rendered content. The overview is
omniscient and does not represent the policy's fog-limited observation.

Across the30frozen games, this model chooses SCV production once overall and never
before180game seconds, despite4774early decisions where SCV production is legal.
Twenty-nine games peak at12workers. These are descriptive trace findings, not yet
an attribution to reward, observations, optimizer or primitive execution. The next
bounded audit will trace SCV preference and credit through saved checkpoints.
