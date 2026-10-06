# Nonlinear human production diagnostic: completed

The fixed tree ensemble and deterministic independent refit completed in46.74seconds; watchdog terminal exit0, peakwholeCPU9.5%, noGPU/native/RL. Saved predictions reproduce on both teaching and development sets. Independent count/error reconstruction validates metrics. No sweep, budget extension or controller promotion.

| Development metric | Majority/mean | Linear state | Tree state |
|---|---:|---:|---:|
| Ability accuracy |37.47%|34.30%|35.95%|
| Class-average recall |5.56%|12.01%|26.34%|
| Nonworker accuracy |0%|15.86%|20.26%|
| Positive-delay accuracy |36.21%|33.62%|34.48%|
| Delay MAE |1.69s|1.72s|1.47s|

Tree predictions recover5/13Barracks,14/44Depots,9/15Refineries,8/10Factories and13/25Marauders, versus linear0,6,0,3,1. Marines fall38→11/217; Medivacs2→0/25. Overall ability accuracy still trails worker-majority. Tree teachingaccuracy84.85% versus development35.95% shows substantial generalization failure. The model uses balanced class weights as well as nonlinear thresholds, so the comparison does not isolate nonlinearity. Better rare-class recall is useful diagnostic evidence, not useful autonomous gameplay.

Per-game developmentaccuracy: SpeCialHas51.75%, uThermalSortOf34.50%, TIMEMaNa30.81%. Nonworker29.89%,14.29%,19.92%. This is the same already-used development split, not fresh independent acceptance.

Keep both forecast model families closed. Current partial teaching data cover only996unique future production events fromsixgames, with1130unresolved original events, and unavailable sensory fields. Before another controller fit, audit additional already-present professional sources for proven player identity, causal fields and production coverage. Retain existing reserved games. Prefer additional varied games with valid observations over extending failed fits; if source coverage cannot grow locally, choose an explicit observation/controller improvement from the audit. No automatic RL transition.

Artifacts: `logs/roadmap/production-threshold-probe-01/` plus guarded execution receipt; scikit-learn1.9.0 already installed in the external environment. Source features/labels/reference files and configuration are hash-bound inreport. No dependency installation or unsafe pickle. Full roadmap remains unachieved.

Final source check reconstructs all3,162stored state/history feature rows exactly
from hash-bound human sources. The final verification receipt binds feature
verification, the tree report and terminal watchdog telemetry. Alljobs are terminal.
