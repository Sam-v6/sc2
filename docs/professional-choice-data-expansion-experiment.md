# Production-choice data expansion

The declared observation-memory comparison failed. This separate experiment adds
five previously acquired professional games to the six-game conditional-choice
teaching set, without changing the weighted current-only model. The additional
games were used in older broad-controller experiments and retain partial sensory
information. They are not fresh evaluation or fully observed replay reconstruction.

## Data verification and frozen comparison

`logs/roadmap/professional-production-choice-02/verification.json` independently
matches all 2,462 examples to original command events and exact current
observations, with human history cleared. Teaching now has 2,173 distinct events
across eleven games, including 383 building events. The original nine games,
including all three diagnostic games, are unchanged example-for-example.
Additional games contribute 906 teaching events and 147 building events.
No future-window duplication or future observation is introduced.

Preparation and verification scripts are `logs/roadmap/prepare_professional_choice_02.py`
and `verify_professional_choice_02.py`. Their source cohorts, source files,
catalogs and output files are hash-bound. Original source outcomes and whole-game
roles are retained. Reserved games are not loaded or predicted. The first verifier
invocation ran before preparation wrote its report and failed on the missing
report; only the final invocation after terminal preparation establishes readiness.

`logs/roadmap/professional-choice-fit-04/contract.json` freezes the comparison
against fit02: fresh seed 822103, current-only shared entity encoder with per-type
status, hidden64, batch16, Adam .001, clip5, game-balanced loss and 30 epochs.
Building/other weights stay exactly 1.7066914922/.8320393497 from fit02; they are
not recomputed from the new teaching distribution. No observation memory,
human command history, failed timing weights or legality masks. Two CPU threads,
GPU disabled, 80% whole-host guard, 900-second optimizer and 1,200-second total caps.

Adding games changes the teaching distribution, equal-game loss normalization
and shuffled batches; this is a dataset comparison, not identical sample order.
The same 30 epochs now expose 65,190 target events, versus 38,010 in the control.
There are no past-frame encodings. This comparison alone cannot separate greater
data diversity from the increased total event exposure.

Frozen gates: accuracy above the expanded teaching-majority baseline; nonworker
recall at least ten points above the old checkpoint on unchanged diagnostics;
building recall at least 40%; at least one correct building per diagnostic game;
false building choices at most 37/235. Existing diagnostic reuse remains explicit.
Independently reconstruct all saved predictions before considering a native
canary. No offline metric proves competent play or permits RL by itself.

## Verified terminal result

`logs/roadmap/professional-choice-fit-04/verification.json` independently
reconstructs all 289 probability vectors and old-checkpoint predictions, original
teaching keys, fixed control weights and gate outcomes. Status:
`verified_failed_professional_choice_fit`. The fit completes 65,190 presentations
in 68.7 seconds, with 8.0% sampled host CPU peak and no guard stop.

| Game | Correct | Nonworker correct | Building correct | False buildings |
|---|---|---|---|---|
| 887 | 13/51 | 7/27 | 4/13 | 11/38 |
| 920 | 77/176 | 44/116 | 11/26 | 20/150 |
| 851 | 33/62 | 13/34 | 7/15 | 10/47 |

Accuracy is 123/289 (42.6%) versus majority 38.8%; nonworker recall 64/177 (36.2%)
versus old 14.7%; building recall 22/54 (40.7%) first clears the 40% gate. Each
game has correct buildings. False building choices are 41/235 (17.4%), exceeding
the frozen maximum 37/235. Thus the model fails overall. Do not waive that gate
after seeing the result. No promotion, native rollout or RL follows.

The subsequent `false-building-resource-audit.json` checks recorded current
resources against the single-product native price for all 41 false building
choices. Twenty-two lack enough minerals or gas even for one product. This
identifies a concrete subset of invalid immediate choices; the other nineteen
are not proven legal (actors, prerequisites, placement and pending construction
remain unchecked). No probabilities, labels or gates were changed. A resource
mask would be a separate declared experiment, not a retrofit of this result;
it must also preserve explicit resource-saving intent in any later scheduler.

Next investigate native expert corrections and legal execution context for the
states the controller mishandles. Keep scripted teacher provenance separate from
professional decisions. Do not reopen arbitrary weight/epoch/memory sweeps or
use these repeatedly inspected diagnostic games as fresh evidence. Human native
competence, broad action imitation, learned micro and RL remain open.
