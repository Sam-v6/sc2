# Human production outcome imitation: offline result

October 6, 2026: the fixed model passes the predefined offline continuation gates.
This is human supervised learning, not RL or native game competence. Native
execution is still required; the full Terran roadmap remains incomplete.

Verified own replay chronology supplies 52 outcome families: construction starts,
trained-unit births, paid Orbital/Planetary completions and completed research.
Starting units, building completion, captures, reversible modes, duplicate tags,
casualties and AutoTurret micro are excluded. Labels describe demonstrated
outcomes, not human intentions. Future events never supply observation features.
The 45-second windows use already verified decision-time observations; samples
are therefore event-weighted and overlapping, not independent time intervals.
These timing definitions are mixed and must be respected by execution accounting:
existing queued trained units/research may contribute future outcomes, whereas a
foundation already started cannot be a future construction start.

Eleven teaching games supply5,378complete windows and the same three development
games supply976. Reserved games remain untouched. All6,354label vectors verify
against tracker chronology; an independently constructed birth/morph/research
index agreed with each original label window. The teaching vocabulary covers
all development targets. Source missing fields remain masked.

One fixed128-tree ExtraTrees regression, leaf4, all features, seed8160, two CPU
threads, no human action history; targets normalized by teaching-only standard
deviation (floor0.1). Prediction uses only masked current state and own type/status.
Fit19.78seconds; CPU-only fit watchdog peak19percent whole-host CPU.

| Development measure | No production | Teaching mean | Model |
|---|---:|---:|---:|
| Macro positive-goal F1 over52families | 0 | .0695 | .2918 |
| Mean absolute count error | .2526 | .2759 | .1592 |
| Building positive precision / recall | 0 / 0 | .5400 / .2202 | .5240 / .5754 |
| Military positive precision / recall | 0 / 0 | .3566 / .7055 | .7579 / .7821 |

All frozen gates pass. Important limits: building count error .1631 remains worse
than the no-production baseline .1431, upgrade recall is only .2963, and numerous
rare families remain weak. The score uses a different target from exact raw
commands; it must not be presented as an improvement on old command accuracy.
These development games were already used for diagnosis, not fresh acceptance.

Independent checkpoint reload reproduced predictions, each family's counts,
precision/recall/error, grouped metrics and every continuation gate. Evidence:
`logs/roadmap/human-production-goals-01/verification.json`, with report SHA-256
`f154ba6e2ebf0822948675b28872cce25e472cb23262115503dc54d622a37dfe`.
The initial-conversion landing regression test exposed a general labeler bug;
its repair leaves all14games' actual labels unchanged, verified separately.

Pending production ledger tests cover no-goal silence, duplicate suppression,
conflicting actor work, acknowledgements/rejections, observed queues, actor loss,
unobserved expiry, queue cancellation and blocked prerequisites. Ledger alone is
not a native executor. Next connect predictions to generic engine-available
production/placement and freeze the six-game development panel before launching.
Declare worker-execution/combat/placement assistance, check live input projection,
and record requested versus fulfilled production, blocks/rejections and outcomes.
Do not invent supply, prerequisites, expansions or army goals in the executor.
RL stays off. Keep broad raw controls for learned micro/full-controller integration.
