# Native command candidates: verified result

The optional `--condition-available` decoder is implemented for GoalFirst.
Normal casts use current resource-aware engine queries across observed own units;
autocast toggles use a separate resource-ignored query and the engine's
`allow_autocast` declaration. Equivalent ability aliases share caster sets.
Learned scores select ability, mode and eligible actors; no depot rule or named
strategy list is introduced. Target and placement validity remain engine checks.
The default decoder, checkpoint parameters and supervised objective are unchanged.
Raw query responses accompany each logged decision, and receipts identify the flag.

New masking tests first failed, then passed. Independent review caught a shared
NumPy/Torch mask mutation before native launch; out-of-place intersection fixes it.
Regression checks verify non-mutation and identical repeated predictions, ability
and actor filtering, empty candidates, default behavior, and resource-independent
autocast. Normal suite: 385 tests, 29 optional skips; focused Torch suite: 21 tests.
Ruff and diff checks pass. Independent implementation and wrapper reviews found
no remaining blockers. The optional test class currently inherits three existing
integration checks; total test counts include those repeated checks.

## Frozen native result

Watcher 22805 and independent verifier 47983 are terminal exit0. One baseline
opening uses the same immutable checkpoint, observation profile, map, opponent,
seed, duration and cadence cap as the prior profile test. It is deliberately
truncated after 180 game seconds, not a completed full game or victory.

- 167 decisions and dispatched commands; no unavailable blocks.
- Three TrainSCV commands and 164 Smart commands; all submissions return Success.
- Three new observed SCV tags; worker count grows from 12 to 15.
- Final minerals 2180, food used/cap 15/15; no SupplyDepot or Barracks appears.
- Whole-host CPU peaks at 6.1%; no GPU, optimizer updates or resource stop.

The verifier reconstructs all decisions from raw observations, the recorded input
profile, both raw engine-query responses and actual dispatched history. It checks
engine aliases, profile/source hashes, prior fit-verification hash chain, frozen
checkpoint, source bindings, decoded arguments, delays and action results.
Evidence: `logs/roadmap/command-candidates-native-01/verification.json` plus its
bound trace, episode, static data, replay, telemetry and checkpoint. Independent
review includes the supervisor cancellation path and reconstruction.

Filtering impossible commands removes the retry loop and reduces callbacks from
2518 decisions to 167, but does not induce useful building behavior. This is not
a timing benchmark: different model choices and schedules change the workload.
The learned policy substitutes legal Smart commands, so the macro failure cannot
be assigned solely to the unavailable-command retry mechanism. Do not extend this
opener or promote either failed fitted controller. No RL occurred.

## Next learning question

The frozen score diagnostic at the first previous supply block assigns TrainSCV
38.1%, Smart 28.2%, Barracks 15.5% and Depot 4.7%. At the final block, TrainSCV is
41.3%, Barracks 31.9%, Smart 11.2% and Depot 3.9%. Forcing the depot ability only
inspects its learned arguments; it does not issue a command or prove buildability.
Evidence: `logs/roadmap/professional-profile-native-01/supply-score-diagnostic.json`.

The current deployment always chooses the single highest-scored ability. That can
collapse behavior to the same command even when other learned choices have
nonzero probability. A next bounded diagnostic could test seeded sampling from
the learned, engine-conditioned ability distribution while leaving argument
selection and weights fixed. It would still be imitation inference, not RL. It
must distinguish valid diverse behavior from random errors, inspect actual
construction/production, and avoid interpreting chance progress as reliable macro
planning. Useful generalization, micro transfer and all difficulty gates stay open.

The earlier observation-contract plan was restored to its exact frozen hash;
post-run prose now lives in a separate results document. Historical source code
is retained in Git (profile implementation commit 8dc6162); newer source changes
require checking out the relevant implementation before rerunning old source-bound
verifiers. Original raw artifacts and model weights remain intact.
