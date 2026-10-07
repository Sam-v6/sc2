# Human prior execution comparison

The matched comparison is independently verified under
`logs/roadmap/human-prior-native-01/verification.json`. Both arms used the same
frozen human count checkpoint and teaching-command pairwise majority prior,
AcropolisLE, Zerg VeryEasy Macro, seed 816003, and a 240-second game horizon.
Both cut off as ties; neither is a victory or useful imitation acceptance.

| Arm | First Barracks | Military births | Living workers at final observation | Peak host CPU |
|---|---|---|---|---|
| A: replacement/opportunistic spending | None | 0 | 27 | 7.8% |
| B: persistent intents/resource reservation | None | 0 | 36 | 5.8% |

B started its first Depot at about 17 seconds, instead of A's late opening.
Replay tracker verification still finds no Barracks or military production.
The trace verifier reconstructs every forecast and priority, resource allocation,
command actor ownership, original intent admission, accepted submission and
observed-order consumption. It checks retries against the same ticket/deadline
and excludes duplicate accepted execution without an intervening timeout.
These are engineering checks, not a guarantee of game strength.

The first actionable failure in B is now concrete. Its Barracks intent was
admitted at loop 0 and expired at loop 1008 (45 seconds). The prerequisite
Depot first made Barracks spending structurally feasible at loop 960, about
42.86 seconds. That frame had 170 minerals; the higher human-ranked SCV consumed
50, leaving 120 reserved toward the 150-mineral Barracks. At expiry it had 145.
At loop 1056 it had 170 minerals and still predicted a Barracks, but the expiry
rule forbade rearming until a zero-to-positive transition. The prediction stayed
positive through loop 1152 and disappeared at loop 1200. This discarded fresh
positive requests precisely when execution became affordable.

The 45-second forecast horizon is not a justified instruction to ignore all
subsequent positive forecasts after an intent expires. The next bounded native
experiment should retain immutable per-ticket deadlines and actor protection,
but permit a new ticket from a fresh positive forecast on a later observation
following expiry. This changes execution rearm semantics, not human weights,
macro priorities, the failed utility gates or the original comparison outcomes.
Freeze its protocol and reuse the same engineering gate before any all-race panel.

RL stays paused. Broad contextual imitation, learned micro and reliable learned
Hard/higher wins remain incomplete. All original A/B artifacts and source snapshots
are preserved. The full suite passed 481 tests with 32 skips; named-file Ruff passed.
