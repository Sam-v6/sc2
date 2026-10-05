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

Status: predeclared; implementation and games have not begun.
