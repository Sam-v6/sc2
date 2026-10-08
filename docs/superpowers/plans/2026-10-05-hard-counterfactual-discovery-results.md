# Hard counterfactual discovery results

The [predeclared experiment](2026-10-05-hard-counterfactual-data-expansion.md)
stops before fitting. All 32 Hard parent games and 47 available one-action
alternatives completed: 79 games, zero process failures. Alternatives were
selected before their outcomes; states with only one non-parent action supplied
one branch, with no replacement or sample extension.

The unchanged parent won 14/32 games. Branch transitions were:

| Parent to branch result | Games |
| --- | ---: |
| Defeat to Defeat | 21 |
| Victory to Victory | 20 |
| Victory to Defeat | 4 |
| Defeat to Victory | 2 |

The two distinct loss-to-win cases were 97013, Protoss, an attack intervention
(discounted return change +.685744), and 97018, Terran, a wait intervention
(+.573197). Both executed with exact parent prefixes. The two-race requirement
passes; the four-distinct-case requirement fails. Return ordering separately
shows 25 positive and 22 negative differences. These are discovery outcomes,
not learned-policy improvements or independent strength acceptance.

The frozen auditor verifies all 43,542 decisions, greedy policy choices except
the single injected alternatives, finite rewards and return telescopes, encoded
prefix caches, selection reconstruction, receipts, replays and unchanged inputs.
It binds completed data with hashes for an independent review. No fitting,
candidate or conditional validation is allowed after this failed gate. The
predeclared 99000 validation bank and reserved 50000 acceptance bank remain unused.

Whole-machine CPU averaged 10.4867% and peaked at 18.4157% across 498 two-second
samples. The four-engine, eight-CPU, nice+10 wrapper remained in force; there
were no CPU cancellations. These samples establish observed load, not a bound
on sub-sample excursions. There was no GPU learner.

Artifacts: `logs/hard-counterfactual-data-expansion/`, including immutable
discovery source/inputs, separate frozen audit source/inputs, raw receipts,
action logs and replays. The separately reviewed future fitting implementation
was never prepared or run. The retained parent remains unchanged.

Independent completed-data review passes and reproduces the complete audit,
including all data hashes and a maximum return telescope error of 1.33e-15.
Receipt: `logs/audit/hard-counterfactual-data-expansion-complete-independent-review.json`.
Reliable Hard strength remains unmet; a further experiment must address a
supported learning mechanism rather than relax this closed discovery gate.
