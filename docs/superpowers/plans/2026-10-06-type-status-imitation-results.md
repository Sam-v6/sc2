# Paired imitation result and native input mismatch

Both thirty-epoch human-imitation fits completed and their predictions, metrics,
initial parity and immutable checkpoints independently reproduced. No RL occurred.
The type-status intervention failed four improvement gates; neither fit is
promoted or extended. Evidence: `logs/roadmap/type-status-imitation-01/verification.json`
and its bound comparison, policies, reports and telemetry.

| Held development metric | Baseline | Type status |
| --- | ---: | ---: |
| Correct macro commands | 27/262 | 32/262 |
| Complete commands | 31/1113 | 26/1113 |
| Macro false positives | 30/851 | 75/851 |
| Correct macro commands with own predicted histories | 10/262 | 23/262 |

These three held games have prior development use. Predicted-history metrics
retain human world states and decision times; they are not live rollouts.
Both fits performed6390updates; optimizer times335.57and430.40seconds.
Whole-host telemetry peaked18.6%; no GPU or resource stop.

## Native behavior inspection

Both frozen policies then completed the predeclared180game-second inspection on
AcropolisLEagainstVeryEasyZerg,seed120602,cap32. These deliberately truncated
openings are not completed full games. Independent reconstruction reproduced
all867decisions, decoded arguments, delays, model-owned dispatched histories,
availability checks and action-result counters. No new observed worker tags,
SupplyDepotsorBarracksappeared; SCVcount remained12throughout logged decisions
and final observations. Baseline issued114Smart/113Attackcommands; candidate
issued320ofeach. Baseline had one rejected command; candidate submissions all
returnedSuccess. Success responses did not imply useful economic behavior.
Whole-host peaks6.7%and6.6%. Evidence:
`logs/roadmap/type-status-native-inspection-01/verification.json`, bound traces,
episodes, static data, telemetry and saved replays. No fitting or selection.

## Frozen opening diagnosis

Compare the native initial state with held human game920'sfirstTrainSCVstate.
Both contain12SCVs, one CommandCenterand the same resource-type counts. Native
SCVorders use ability295(HarvestGatherSCV); the replay uses3666(HarvestGather).
Both static catalogs explicitly remap295to3666. The encoder currently embeds
these orders as different IDs. Native inputs also expose fields that the partial
replay does not expose. Map, positions and other input differences remain.

A read-only factorial check keeps the saved weights fixed. It removes native
fields according to that source's declared availability and/or changes only
SCVmining-order IDs to the catalog's equivalent generic ID:

| Native opening input | Baseline SCV probability | Type-status SCV probability |
| --- | ---: | ---: |
| Original | .0184 | .0341 |
| Source field availability only | .1917 | .1945 |
| Generic mining-order ID only | .0627 | .1774 |
| Both | .5877 | .5348 |

Only the combined change switches both opening predictions toTrainSCV.
Setting native time to the human issue loop17does not repair the original
prediction. Source-state SCVprobabilities are.5630/.5496. This isolates a real
representation discrepancy and an initial prediction effect, not a full-game
causal explanation or a justification to promote either failed model.
Evidence: `opening-mask-diagnostic.json` plus its source/checkpoint/script hashes
under the native inspection directory. The diagnostic uses the previously used
held game920; no reserved replay is consumed.

Next implementation should make a professional-trained model's observation
contract explicit at native inference: equivalent order IDs and field availability
must be handled consistently. Keep full native observations in traces, retain raw
command grammar, and make any partial-source compatibility projection explicit.
Test equivalent-order behavior and non-mutation, then verify whether the correction
produces an actual worker in a bounded native opening. No further controller fit
or RL is justified by these results alone. Useful imitation, learned micro transfer,
reliable all-raceHardwins and higher-difficulty evaluation remain incomplete.
