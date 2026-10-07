# Immediate production choices with resource checks

Fit04 remains a failed unfiltered model. This separately declared inference audit
keeps its weights and probabilities fixed and removes only known single-product
production prices exceeding recorded current minerals or gas. No optimizer, new
labels, RL, native game or checkpoint modification is involved.

The rule addresses immediate issuance, not longer-term plans. Unknown prices stay
unknown and remain eligible in this audit; generic research tiers are not guessed.
Do not replace a separately selected resource-saving plan with a cheap unit.
Do not describe this mineral/gas check as complete native legality.

`logs/roadmap/professional-resource-filter-01/contract.json` freezes the rule and
existing gates before evaluation. Its `verification.json` has status
`verified_resource_only_inference_gates_passed`. The independent verifier loads
the unchanged NPZ, reconstructs all 289 probability vectors from original current
observations without human history, reconstructs prices from the bound historical
execution code, and independently derives the blocked set and filtered argmax.
It also compares the new production helper against that independently derived set.
All metrics and per-game counts reconstruct exactly.

| Check | Unfiltered fit04 | Resource-only choices |
|---|---|---|
| Overall correct | 123/289 (42.6%) | 144/289 (49.8%) |
| Nonworker correct | 64/177 (36.2%) | 70/177 (39.5%) |
| Building correct | 22/54 (40.7%) | 22/54 (40.7%) |
| False building choices | 41/235 (17.4%) | 21/235 (8.9%) |

Thirty top choices change. The resource-only result passes accuracy above majority
38.8%, nonworker improvement above old 14.7% by ten points, building recall 40%,
correct building in every diagnostic game, and false buildings no more than
37/235. These are repeatedly used diagnostics, not fresh generalization evidence.
The original result and gates are retained; the failed model is not relabeled as
an unfiltered success.

Among the original 41 false buildings, 22 lack single-product resources. All 41
have a currently observed completed SCV and any catalogued building prerequisite.
These observations do not establish a free actor, correct placement, engine
availability or absence of pending construction. Missing attachment, queue detail
and exact source supply usage remain unresolved.

The small `resource_affordable_choices` helper preserves remaining scores,
accepts exact-budget boundaries, checks gas and minerals, keeps unknown prices
without guessing, and returns an empty set rather than inventing an action.
Two new tests were observed failing before implementation. All 16 production
execution tests and the default 587-test suite pass (40 optional skips); Ruff and
diff checks pass. It is not wired into native play yet.

Reproduction scripts:
`logs/roadmap/audit_professional_resource_filter_01.py` and
`logs/roadmap/verify_professional_resource_filter_01.py`. The original execution
module is preserved in the audit's source snapshot: adding the helper changed the
live file hash, so historical price bindings are checked against the exact old
bytes; the current helper is separately bound and checked for equivalence.

Next run a bounded native conditional-choice canary with the verified primitives.
The model chooses a production ability; the execution layer must query real owned
actor availability, verify resources and placement, track an accepted request to
its observed effect, and preserve separate attribution for mining, scouting,
reactive supply and combat. Use the matching partial observation projection for
model features while retaining complete native observations for execution and
traces. Do not substitute scripted worker/army/Barracks quotas for model decisions.
Declare fixed cadence and actor/target primitives. Native availability is an
additional execution guard, not evidence that the offline source had those queries.
If native behavior fails, inspect the first choice-to-effect divergence and
collect explicit expert corrections. Useful native imitation remains required
before RL or Hard strength claims.
