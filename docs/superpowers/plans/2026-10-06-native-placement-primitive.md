# Execute learned construction points through the existing placement primitive

The fixed sampled imitation opener chooses a depot/refinery that complete, but
three CommandCenters and a Barracks fail with CantFindPlacementLocation. Integrate
existing resolve_placements explicitly, without changing learned build choices,
worker groups, queues, sampled probabilities or weights. Default remains unchanged.
The existing helper ranks nearby half-tile candidates and visible resource positions
by distance from the requested point, then asks the engine about placement.

Add opt-in --engine-placement. Record original model command, actually dispatched
command, helper decision and exact placement requests/responses. Dispatched history
must contain the adjusted command, not the intended illegal point. Rejected placement
is not dispatched or put into history; count it separately from ability blocks.
Record adjustments/rejections in receipts. Construction to unit targets and other
non-point commands retain current behavior; no invented conversion or build order.

RED then GREEN integration checks: real adapter callback with fake engine verifies
adjusted dispatch/history/provenance; rejection does not dispatch/update history;
default does not query/adjust. Existing primitive tests cover local legality and
preservation of action/group/queue. Full normal/focused tests and independent review.
Then one frozen baseline opener using same profile/candidates/ability seed120603,
map/opponent/game seed120602/cap32,180game seconds/120wall seconds/twoCPUthreads/
80%wholeCPUguard. Independently replay recorded placement packets to reconstruct
requests, helper choice, sampled model prediction and actual dispatched history.
Check real structure construction/production, not success codes alone. No fitting,
seed sweep, promotion, win claim or RL. Keep plan immutable and write results separately.
