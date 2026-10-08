# Queue reservation correction: saved-state pass, native canary failed

October7,2026. Read-only Astra advice identified a real inconsistency in the fixed
human executor: it admits training into queues at full supply, but its older-request
budget protection excludes those requests when free supply is insufficient.

The frozen native25 trace shows Cyclone ticket181 has its ability available at10488,
but only135 minerals. At10504, the bank reaches175 and later PlatingLevel2 ticket188
spends175. At10512 the bank is15; the Cyclone deadline expires10552 with90. Its
Factory is complete, bound, empty and has the required addon in both saved states.
The block label `earlier_resource_commitment` also covers simple unaffordability,
so the label alone was not used to establish the cause.

## Bounded correction and result

The candidate protects an earlier Train request only after resolving its owned
producer and querying current exact native ability availability with resources
ignored. Full supply alone does not remove protection. Unbound/lost actors and
native-unavailable abilities do not gain unconditional reservations. Explicit
reactive Depot priority remains possible. Trace budgets expose protected ticket,
price and held resources; direct unaffordability has a separate label.

Saved-state regressions pass the10504 budget case, missing/native-unavailable
producers and the Depot exception. Candidate full suite553 tests/32 optional skips
and Ruff pass. One matched canary27 preserves plan06, seed817501, original gas,
reactive supply, horizon and30-second deadlines.

The **native repair gate fails**. It stops earlier at7848 on Factory ticket96
(source7171), with native placement result44.109/247 instructions resolve.
A supplementary Depot issued7144 begins at7216 and completes7696, centered(136,37).
That occupied footprint intersects the source Factory target(134.5,37.5). The
Factory's requested point is fixed by the human replay; the executor cannot place
it there once the native layout changes. No command action errors are recorded;
three supply warnings retain matching zero-progress queues. CPU peaks8.4%.

The run never reaches Cyclone181. It cannot prove successful native queue admission
for that request or compare worker births at9224. At the shared6000 cutoff both
runs have33 SCV births and zero confirmed worker supply stalls. The independent
receipt explicitly records `repair_success=false` rather than treating verifier
completion as a passed gameplay gate.

The candidate is **not promoted**. Its code and regressions are archived under
native27/source-snapshot; tracked execution and tests are restored to18387a4.
Do not run another priority sweep, extend the deadline, silently reserve future
human construction coordinates, or claim the original247-ticket witness passed.

## What this changes next

Exact replay playback has now exposed useful source, queue, addon, construction,
landing, supply and reservation cases. It also exposes a limit: changed spending
and survival alter supply timing and geometry. Keep the witness as a regression
corpus and its original gate incomplete. It should not become a strategy optimized
for one fixed opponent or an indefinite prerequisite for every learning experiment.

Return to state-conditioned human imitation through the verified primitives,
retaining rich unit/map/order observations and broad raw commands. In the next
experiment, the policy must request production from the current game state, while
construction selects a currently legal location and source-specific addon identity
is not supplied as hidden future information. Carry supply25 as an explicitly
scripted assist; evaluate complete learned commands, sustained workers/army,
construction interference and actual games. No current offline or scripted result
establishes learned Hard or higher-difficulty competence. RL remains gated on
useful native imitation.

Evidence: `logs/roadmap/fixed-human-plan-native-27/verification.json`, contract,
replay, trace and bound code snapshots; `verify_reservation_native_27.py`.
Native25's original receipt remains intact. Adviser recommendation is retained in
this conversation. All simulations are terminal; no fit or RL was launched.
