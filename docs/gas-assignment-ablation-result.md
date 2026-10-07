# Steadier gas assignment did not fix the funding stall

October7,2026. The supply-assisted fixed human witness25 still stops at10552 on
Cyclone source instruction9874. This follow-up tests a possible income problem;
it does not fit a model or run RL.

The original gas rule targets either zero or three workers per completed Refinery.
It pauses gas when the bank exceeds400 gas and minerals are below200, then resumes
as soon as that condition clears. Between9000 and10552, native25 changes quota four
times, including18→0→18→0→18. Its observed mining commands contain69 resource-type
switches;18 switches on14 workers follow another mining command within224 loops.
These command observations do not by themselves prove lost income.

Native26 uses the same plan, seed817501, opponent, supply assist and deadlines.
Its explicitly experimental gas rule remains paused until gas falls below200 or
minerals reach400. It reduces observed late switches69→43 and fast switches18→9,
but it **fails to improve the production witness**:

| Same cutoff / measure | Supply control25 | Steadier gas26 |
| --- | --- | --- |
| SCV births before6000 |33|33|
| SCV births before8800 |50|50|
| SCV births before9224 |53|51|
| SCV births before10552 |66|65|
| Confirmed worker supply-stall producer-seconds before9224 |10|25|
| Resolved source instructions |187/247|188/247|
| Cyclone funding stop |10552|10552|
| Mineral collection rate at10400 |2883/min|2743/min|
| Peak whole-host CPU |8.1%|8.3%|

Neither run loses SCVs. Native26's three final births are at10551,10551,10552;
its final player worker count66 therefore differs from65 tracker births before
the exclusive cutoff10552. Comparing exact cutoff definitions matters.

Both runs retain seven matching zero-progress production/supply warnings and have
no other recorded action errors. Native26's third extra Depot starts but does not
finish before the forced exit. All snapshots, replay seeds, source hashes, actual
Depot foundations and worker-birth comparisons are independently verified.

The experimental gas option and its temporary regression test are removed from
tracked code. The retained gas behavior is unchanged from18387a4. Its bound code
remains in native26/source-snapshot for reproducibility. Fewer worker switches is
not enough to justify promoting it. No further gas-threshold sweep is authorized
by this result; investigate the remaining resource scheduling/timing mismatch.

Evidence: `logs/roadmap/gas-reassignment-25/audit.json`,
`gas-reassignment-26/audit.json`, `fixed-human-plan-native-26/verification.json`
and the archived auditor/verifier scripts. The candidate suite passed552 tests
with32 optional skips; retained code is byte-identical to the previously verified
551-test baseline. Imitation and RL remain paused; full roadmap stays incomplete.

A separate [reservation correction canary](resource-reservation-canary-result.md)
also fails its native gate and is not promoted. Both candidates remain archived;
tracked execution retains the supply-assisted18387a4 behavior.
