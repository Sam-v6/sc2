# Connect the human imitation controller to the headless runner

The latest read-only audit reconstructs saved-model training loss and gradient:
state macro recall4–7%, history80–84%, both92–94%, despite weak held-game
scores. This supports investigating representation/generalization; incomplete
solver convergence prevents a sufficiency claim. Do not refit closed probes.

Separately, GoalFirstPolicy cannot run through entity_play: the existing driver
loads JointEntityPolicy and reads its NumPy encoder schema. Close this necessary
roadmap gap before another checkpoint needs native evaluation. This is execution
infrastructure, not a model promotion, experiment fit, or RL.

- Add an explicit optional --controller goal-first; preserve joint default.
  Import optional Torch only when selected, with existing safe NPZ loading.
- Expose derived native input dimensions on GoalFirstPolicy so the shared
  command agent builds matching masked/spatial inputs. Validate engine unit,
  ability and upgrade vocabulary before issuing any model command.
- Reuse existing decode, issued-only command history, delays and availability
  query; do not add scripted macro or change raw action choices.
- Test RED then GREEN: actual tiny goal-first predictions through the shared
  agent, raw actor tags/world targets/queue/delay, checkpoint loader parity,
  engine mismatch rejection and optional dependency isolation. Run appropriate
  normal and optional Torch tests; independent review before committing.
- Do not run a strength panel or promote the failed professional checkpoint.
  Functional native smoke/transfer and reliable Hard wins remain unproved.

The first adapter still issues one command per observation; same-observation
batching and full contextual command-roster execution remain roadmap work.

Review found no blockers; strengthen the native guard to reject wrong history
role width or point-feature layout before issuing commands. Focused tests cover
these failures. One15game-second native smoke is authorized infrastructure
validation: failed frozen professional checkpoint, installed local engine,
VeryEasyZerg, seed120601, AcropolisLE, wait-unavailable,60second supervisor,
80%whole-host guard/two threads/noGPU. Inspect immutable checkpoint, trace,
commands/action results and saved replay; no strength conclusion or promotion.

## Verified result

Adapter implementation and all14focused optional-runtime tests pass. The normal
372test suite passes with23optional skips. Ruff and whitespace checks pass;
independent review found no blockers. Native schema also rejects unsupported
history-role/point layouts. The installed75689engine has the same vocabulary
(1970,3801,296) as this professional-derived checkpoint, and passes the guard.
This does not imply identical producer-version semantics or complete source
observations.

The bounded native smoke completed336frames and15game seconds in9.731wall
seconds, deliberately truncated. All11issued commands returnedSuccess; all
wereSmart. Every decision/decoded command/delay/issued-only history entry was
independently reproduced from the unchanged checkpoint. Saved replay is nonempty;
CPU peaked6.1%. No videos shown. This proves adapter wiring, not macro competence,
full-game performance, micro transfer or Hard wins.

Use `python -m src.learning.entity_play --controller goal-first --policy ...`
with the existing optional CPU Torch runtime and an explicit fresh output/map/
time bound. The defaultjointpath retains its NumPy-only loader. No strength
panel is justified by this smoke.

- `logs/roadmap/goal-first-native-smoke-01/episode.json`: `1a0967d4aca7a9ec9e4584facde1ada7e65b21fd820b36b7bb5649a31d7cda54`

- `logs/roadmap/goal-first-native-smoke-01/verification.json`: `6fb35ee41760df046c1632f4bd31ba539c93052fad00510c280d40c4d94a98ec`
