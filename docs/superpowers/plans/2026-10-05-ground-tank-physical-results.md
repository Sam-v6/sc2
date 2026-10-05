# Ground-aware tank physics: recorded requirements verified

Native session7612 terminates exit0 after all6isolated debug fixtures127000–5,
with138observed frames/native replays and no optimizer or macro loop.
The original frozen summary is **failed**, because case127005's exact target
type checker did not recognize the computer lowering its SupplyDepot.
Original source, receipts and summary remain unchanged.

The separate independent semantic audit verifies all recorded physical
requirements, recognizing only the SupplyDepot/SupplyDepotLowered family with
one stable visible target tag. It preserves the original failure and changes
no geometry, frame, command or observed-siege requirements. No new native games
were needed. Root's separate optional offline interpretation agrees, but the
independent audit supplies the authoritative physical finding.

| Case | Recorded contextual physical behavior |
| --- | --- |
| Original mobile tank, air | 21sieged/22context frames |
| Corrected mobile tank, air | 7mobile/0sieged frames |
| Original sieged tank, air | 22sieged/0mobile frames |
| Corrected sieged tank, air | 21mobile/1sieged frames, unsiege queued |
| Corrected tank, Roach | 13sieged/15context frames, siege queued |
| Corrected tank, lowered depot | 20sieged/22context frames,2siege commands |

The correction considers visible non-flying enemy units/structures at the
existing12/14ranges. The adapter retains the other original micro operations;
tests verify unchanged Marine/Medivac/Raven commands. Medivac healing remains
unchanged because the preceding native trace showed actual healing.

CPU13two-second whole-machine windows: mean10.5038%, peak14.6847%.
The2worker fixture bank is engineering evidence only: no ordinary opponent
victories, learned improvement or Hard acceptance. No replay was opened.

Evidence: `logs/ground-tank/physical-fixture/`,
`logs/audit/ground-tank-fixture-complete-independent-review.json`, and its
separate semantic audit source. Next is the independently frozen24game matched
ordinary comparison; physical behavior alone cannot establish win effects.
