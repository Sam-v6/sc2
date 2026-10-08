# Observe combat primitives before changing them

The completed macro teacher bank is closed and fails its all-race gate.
Its raw queues show repeated medivac movement and tank siege checks against
all nearby enemy units. Queue records alone do not establish actual healing,
engine orders or why Terran battles fail. Resolve those uncertainties before
changing combat behavior or collecting imitation targets.

Run exactly4fresh observation-only Hard Terran games, seeds126000–126003,
policy seeds identical. Builds are Rush,Timing,Air,Macro; maps are
Simple64,Simple64,TritonLE,TritonLE. Use the unchanged closed selector/executor,
27actions, nominal1second macro cadence, game_step8, reward and fog/resources.
The context checkpoint remains frozen-easy40 and supplies no teacher weights.
No outcome gate, bootstrap qualification, fitting, tuning or model promotion:
additional wins cannot change the failed12game feasibility result.

A new observer records current own medivac/tank health, energy and engine orders
before commands are queued, visible ground/air unit counts within12and14,
ground structure counts within14, and nearby own
biological unit health/distance. It calls the original observer exactly once
and issues no commands. Preserve ordinary actions/rewards/journals/native
replays and typed scripted data explicitly forbidden as on-policy PPO input.
Queue entries remain distinct from observed engine orders.

Source review and tests precede freeze/launch; bind source, maps, context and
prior complete audit. Freshness scan covers all3existing artifact roots.
Use4workers, eight-CPU affinity/nice10, one numerical thread, no GPU,
80%whole-machine ceiling/50%baseline,1200game/180wall seconds per game.
Preserve every submitted outcome on interruption/error; never rerun this bank.
Reserved final cases50000–50029remain untouched. Keep replays unopened.

After terminal completion, check native evidence and summarize medivac orders
when nearby wounded biological units exist, energy/health changes and siege
orders in air-only neighborhoods. These describe behavior, not causal win-rate
effects. Any primitive change needs separate targeted tests and a fresh matched
comparison; teacher strategy is not tuned from these diagnostic outcomes.
