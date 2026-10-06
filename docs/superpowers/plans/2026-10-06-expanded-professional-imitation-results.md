# Expanded professional imitation result

Closed October 6, 2026. The frozen human-imitation experiment completed but
failed all learning gain gates. No native evaluation or RL followed.

Training used eleven professional teaching games, 6,089 raw decisions and 6,086
representable decisions. All 30 epochs, 6,390 updates and 101,940 presentations
completed in 418.84 optimizer seconds. Every representable example was exposed.
Teaching-only support changed alongside the corpus, so this comparison does not
isolate the causal effect of adding data.

On the same previously used development games, production ability correctness
changed from 21/262 to 27/262; complete commands from 28/1,113 to 30/1,113;
and own-history production correctness from 4/262 to 3/262. Production false
positives decreased from 33/851 to 27/851. Completed-budget and false-positive
gates passed; macro, complete-command and own-history gain gates failed.
Correct production choices were 26 SCVs and one Marauder, with no correct
building choices. This is not useful imitation or native game competence.

Independent verification reloaded the checkpoint and reconstructed 7,202 ordinary
predictions, 1,113 own-history predictions and the exact sampling/exposure schedule.
Receipt: `logs/roadmap/expanded-professional-imitation-01/verification.json`.
Contract SHA-256:
`8657b1b9d6f7b5582acea8a7d2ae70afaf8a747cb244f234daa10fa849f96373`.

The CPU-only two-thread fit peaked at 93.3 percent whole-host CPU. The first
verification stopped after three consecutive samples above 80 percent. A retry
waited for headroom and completed, with an isolated peak of 99.6 percent. The
guard permits transient peaks and is not an instantaneous ceiling. No GPU used.

Do not extend or repeat this unchanged fit. Advisory next direction: supervise
simultaneous short-horizon production outcomes from verified own chronology,
then execute through generic goal accounting. This needs a frozen label contract,
baselines, accounting tests and an offline pass before a bounded native panel.
It is a proposal, not an implemented result or an RL promotion.
