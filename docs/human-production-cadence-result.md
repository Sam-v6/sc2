# Recent-fulfilment cadence diagnostic

The frozen 600-second Zerg VeryEasy Rush canary (seed816201) and independent
verifier are terminal. Evidence is in
`logs/roadmap/human-production-cadence-native-01/verification.json`. Sources are
archived separately from the earlier all-race panel. No model fit, training or RL.

Replay confirms 14 Depot starts, 68 living workers and 34 military births;
Barracks start is 50.76 seconds. The original opening engineering gate passes.
The result is a horizon Tie, not Victory. CPU peaks at 8.0%; wall time is49.094
seconds. Full suite485tests/32skips and named-file Ruff pass.

Compared descriptively with the old Zerg Rush game (different seed), Depot starts
fall from54to14 and final workers from90to68. The trace verifier reconstructs
original forecasts, observed order fulfilments and their1008-loop age-out,
maximum(history,current queue) accounting, accepted tickets and native production.
It does not count rejected/lost/unechoed actions as fulfilments.

The strict predeclared one-Depot cadence gate is **false**, because this changed
trajectory sometimes forecasts two Depots. Shorter-than45-second gaps occur in
those windows. All14observed Depot orders have verified origin and quota accounting;
do not rewrite the frozen strict gate or claim it passed. A future conditional
cadence criterion would be a new protocol, not retrospective acceptance.

The larger remaining problem is under-demand for production capacity. At the
horizon the bot has one Barracks, one Factory, one Starport and about7050minerals/
4078gas banked. Primitive command execution cannot spend those funds without
learned demand. The count predictor still rarely requests more production buildings.
Rate accounting reduces one overspending failure but does not make this model
competent or full professional imitation. Do not repeat this unchanged run or
resume RL. The next representation should explicitly learn desired human army/
economy/production inventory, with canonical mode/morph accounting, rather than
trying to infer all macro from averaged next45-second birth counts. Freeze and
verify a new teaching contract before fitting; preserve failed historical gates.
