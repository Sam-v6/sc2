# Validate the model's exact unit-target construction position

All three rejected refinery commands in the previous trace target geysers sharing
an exact visible position with an existing ownRefinery (two complete, one building).
Add engine placement validation at that selected visible target's exact position.
This tests actual placeability without changing the chosen geyser, ability, worker,
group, queue or command mode. Never search for a different unit target.

Reuse the opted-in existing resolver. Point construction behavior stays unchanged.
For unit-target construction, query exactly one point from the currently visible
selected unit. If legal, return the original command; if rejected, return none and
record unit target, position and engine result. Unknown/unobserved targets must not
produce a speculative position or hidden-state query. Preserve packet recording,
separate placement counts and actual dispatch history in the native adapter.

RED/GREEN tests for accepted exact unit target, rejected occupied position, missing
visible target and unchanged existing point behavior. Full normal/focused tests,
independent review. One frozen baseline opener with existing profile/candidates/
placement/sampling seeds120603/120602, map/opponent/cap32,180game seconds/120wall,
2CPUthreads/80%wholeCPUguard. Independently reconstruct all point/unit placement
queries and history, inspect actual production/construction, and distinguish
precheck rejections from successful engine submissions. No training, seed sweep,
extension, checkpoint promotion orRL. Write results separately from frozen plan.
