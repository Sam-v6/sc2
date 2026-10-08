# Why the human production opening stalled

The scripted baseline remains 30/30. The fresh human-production bridge failed
its four-minute native engineering canary: resources were collected, but there
was no Barracks or army. RL remains paused.

Two additional audits narrow the next intervention. Their artifacts are under
`logs/roadmap/`; neither is a native causal experiment or a competence claim.

## The missing Depot is not explained by the clock alone

`human-goal-native-03/opening-sensitivity.json` holds the original opening entities
fixed and varies only game time (loops 0 through 3408) and minerals (50, 100, 150).
The frozen model continues to request a Depot and Barracks in every tested state.
This rules out those isolated input changes as a sufficient explanation in this
diagnostic. It does not identify which other feature caused the request to vanish,
and the edited states need not be physically reachable.

All eleven teaching games started a Depot at approximately 17–20 game seconds,
before their first Refinery. Our canary started a Refinery first and deferred the
Depot until approximately 152 seconds. Its observations therefore depart from the
human opening sequences. Treat the apparent dependence on opening progress as a
hypothesis, not proof of a particular model feature's causal effect.

## Resource commitments need different labels

`human-production-commitments-02.json` maps 1,970 original human production commands
in fourteen teaching/development games through the native catalogue, using the
actor's type to resolve generic addon aliases. No mapped command has an ambiguous
family. The first opening commands consistently alternate worker training with
Depot construction, then Refinery or Barracks construction. Their ordering is
missing from the simultaneous future-count target.

These are issued intentions, not guaranteed production: duplicate attempts,
cancellations and unavailable actors must be accounted for in a training target.
The audit does not silently relabel them as successful starts.

The existing outcome-timing experiment is already terminal. Its saved report and
all bindings match current files. Its reported development timing error is 12.34
seconds versus 11.23 for a teaching-family median; both the baseline and group
quality gates failed. It mixed building starts, unit births, and upgrade/morph
completions. Those events describe different stages of resource expenditure.
Do not repeat this fit unchanged or load it into live play.

## Next intervention

Keep the passing count checkpoint and failed canary frozen. Learn the relative
order of actual human production commitments, and maintain unique outstanding
requests through resource/prerequisite delays. Ranking, persistence, resource
reservation, successful starts and cancellation must be separately auditable.
Execution must not invent prerequisite or army goals and call them learned.

Astra was consulted under the user's explicit advisory authorization after the
raw-command, count and outcome-timing approaches failed to provide useful native
imitation. Its advice is subject to the same evidence and bounded native checks.
