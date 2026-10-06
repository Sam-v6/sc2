# Frozen human-policy native execution diagnostic

Goal: identify concrete closed-loop command/execution failures in the completed spatial human imitation policy, without optimizer updates or a strength acceptance claim.

The previous goal turn made progress: spatial fit/comparison completed with exact reload verification, and the native adapter passed offline review plus two artificial SCV fixtures. Human-state copying improved to1896/4190complete commands but transfer and exact groups remain weak.

Ruling: retain the frozen95%ability/90%groups/75%complete gate for promoting imitation and starting RL. Earlier plans also held every learned native run; amend that restriction to permit bounded, unpromoted execution diagnostics. Teacher-state errors alone cannot identify native coordinate validity, command availability, construction interruptions or divergence of the model's own history. This is an implementation diagnostic, not a lowered competence criterion, fresh acceptance bank, human holdout use or RL.

- [x] Bind completed fit05 checkpoint/source/configuration and current executor code before the run.
- [x] One60-game-second episode, AcropolisLE, VeryEasy Zerg/RandomBuild, seed130001, wall90s, game_step1, CPU-only two BLAS/OMP threads. No debug game setup, worker/placement/micro assistance, ability resampling or model updates. Preserve trace/replay; no display.
- [x] Verify terminal supervisor state and unchanged bindings. Count native results by predicted ability/target mode, compare intended actors with queried availability, inspect worker/building state and model-owned causal history. Retain failures as failures.
- [x] Record the next intervention from concrete evidence; no Hard win/promotion/generalization claim from a short single episode.

All full professional imitation, sensory completeness, learned micro transfer, reliable all-race Hard and higher-difficulty requirements remain open. Reserved human replays51483/51886 remain closed.

Verified result: baseline completed its planned cap with 11 successes and two unavailable-command rejections. The opt-in retry comparison used the identical checkpoint/map/seed/duration: 48 decisions, 35 unavailable intentions withheld, 13 issued commands all accepted. All 48 decisions reproduce exactly from the frozen checkpoint and issued-only history. The Supply Depot completed; Barracks and Refinery started, but remain unfinished at 60 seconds. No army or win evidence. Checkpoint and paired code/source bindings unchanged; replay 9708 bytes. Receipt: `logs/roadmap/joint-frozen-native-wait-verification-01.json`.

Next bounded diagnostic: same checkpoint and setup with availability retry, 180 game seconds / 120 wall seconds, seed130001. Freeze bindings before launch. Inspect building completion, army production, engine results and construction-worker orders. This remains inference only and cannot authorize RL or satisfy strength acceptance.
