# Execute complete commands from the shared imitation model

Goal: provide the live-game path missing from the joint imitation model. The existing native player loads the older factorized policy. Do not add recipes, forced harvesting, placement overrides or scripted combat.

- [x] Add and test a small execution adapter using current fog-safe `state_inputs`, model-owned history, `decode_command`, learned delay and exact raw tags. History stores known target positions when issued; native action echoes must not duplicate it.
- [x] Add a supervised headless game entry point that loads the joint checkpoint, checks engine vocabulary, feeds the same static/dynamic grids, logs raw decisions/results, preserves a native replay and reports terminal status through the existing bounded supervisor.
- [x] Test offline command/history/cadence behavior and checkpoint path. Native learning evaluation remains held while teaching prerequisites fail; this adapter is infrastructure, not evidence of competence or permission to restart RL.

Develop the new adapter independently while fit05 handle60586 runs. Do not edit the live fit's bound files. Keep the full professional/micro/Hard/higher-difficulty roadmap intact. No download/sudo/GPU.

## Verified implementation

`entity_execution.py` uses its own issued history, preserves raw tags/groups/targets/queue/autocast through the existing decoder, and uses the model's delay. `entity_play.py` validates vocabularies, captures the actual pre-decision history in traces, feeds native static/dynamic grids, uses the existing bounded supervisor and saves a replay. It issues one command per observation; zero delay advances one loop, so same-observation batching/increased micro throughput remains open. No worker, construction, placement or combat assistance.

Tests were observed failing before both adapter/schema implementations. Full suite241tests in9.981s; Ruff/diff checks green. Independent reviewer found no actionable defects, passed54entity/6gameplay tests, and additionally checked checkpoint reload/autocast/uint64 tags/echo exclusion/history/cadence offline.

Two artificial checkpoint fixtures (coordinate-only and spatial-enabled) each reached the planned30game-second time limit on AcropolisLE against VeryEasy Zerg:672frames,21SCV-production commands,6native Success responses and15NotEnoughMinerals responses. Both saved nonempty native replays. This tests SCV command plumbing, not other native target families or learned play. Receipts: `joint-native-fixture-verification-01.json`, `joint-native-spatial-fixture-verification-01.json` under `logs/roadmap/`. Exact causal history counts and checkpoint/replay hashes verified; spatial trace conversion produces506x386features. Fixture handles47729/9052 are terminal. There was no learner evaluation, optimizer, RL, download or replay display. Task4's learned construction/army demonstration remains unperformed.
