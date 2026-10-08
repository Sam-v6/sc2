# Terran macro reinforcement-learning experiment

## Intent and scope

Build a reproducible headless learning experiment against computer opponents. Terran
macro decisions must come from a learned policy. Scripted primitives can execute
build/train orders, assign workers, and control units in combat. This is an explicit
first experiment, not the final observation representation or action space.

Observations are collected during the game, not only at game end. Include resources,
supply, worker/army composition, production, technology, expansion count, visible
enemy composition and positions relative to our bases. Respect fog of war. Log
observations and policy actions so blind spots can be inspected in replays.

Start with a small NumPy learning implementation to avoid installing a large ML
stack. Compare learned, random, and scripted policies before deciding whether this
representation is useful. Do not call the scripted comparison an RL achievement.
Future experiments may replace the encoder with spatial observations and the
learner with a neural policy without changing game-result/replay evidence.

## Acceptance

- A real SC2 game terminates, writes a nonempty replay, and reports its outcome.
- Training produces policy updates and a checkpoint; resume preserves learning.
- Frozen evaluation changes no policy parameters and consumes separate seeds.
- Hard evaluation spans Terran, Protoss, Zerg and declared AI build types/maps.
- Initial success target: at least 70% wins in 30 frozen Hard games, ten per race.
  Also report per-race results and uncertainty; thirty games are only preliminary.
  Report failure honestly and continue bounded experiments instead of labeling
  timeout, exception, or short smoke-test ties as victories.
- A saved replay can be exported to an MP4 on this Linux installation.
- Report measured wall time, simulated time, startup, decision count and failures.

## Audit on 2026-10-04

The root checkout was clean at `9d05cac`, branch `feature/setup-infra`. There was
no test suite, no training code in this repo, and an empty README. The runner
contains two successive hardcoded experiment configurations; the second overrides
the first. It chooses sixteen supervisors on this 32-CPU host, starts a new SC2
process per game, kills only its Python worker on timeout, and uses timestamp-only
replay names that may collide. DEV mode grows a pandas DataFrame every step.
`src/path.py` assumes the game lives immediately above the checkout, which breaks
inside a worktree. SC2 imports precede path setup in the runner.

Sibling folders:

| Location | Role | Treatment |
| --- | --- | --- |
| `../game/SC2.4.10/StarCraftII` | Installed Linux SC2, build 75689, maps | Reuse externally; document SC2PATH |
| `../environment.sh` | Old SC2PATH export | Document as legacy; no deletion |
| `../requirements.txt` | Old dependency list | Document as legacy; no deletion |
| `../SC2RL` | Separate Protoss PPO tutorial, models and logs | Preserve as reference; no migration of old weights |
| `../pysc2` | Separate learning environment checkout | Optional reference, no runtime dependency initially |
| `../sharpy-starter-bot` | Separate scripted bot project | Preserve as reference |

The old SC2RL trainer uses shared-file pickle polling, unbounded waits, subprocess
launches via `python3`, image observations and OpenCV display calls. Its Protoss
weights are not a Terran starting policy. Its environment step handshake also
appears to read state before waiting for the bot to consume the submitted action;
do not carry that synchronization design forward.

No SC2PATH was exported in the inspected process environment and no SC2 export was
found in `.bashrc`/`.profile`. The existing Python 3.12 environment imports BurnySC2
and NumPy, but lacks torch, SB3, Gymnasium, pytest and s2protocol.

### Verified probes

`/tmp/sc2-void-audit/smoke.py` ran Terran vs Hard Zerg on Simple64, seed 7,
with game step 32 and a 60-game-second limit. It completed in 6.59 wall seconds,
42 callbacks, and saved an 8.2 KiB replay. The result was a time-limit Tie, not a
competitive game or performance comparison against the old runner.

`/tmp/sc2-void-audit/render.py` used the existing `libOSMesa.so.8`, replay bytes,
and map bytes with RequestStartReplay. SC2 returned `in_replay` and a nonempty
640x480, 24-bit RGB observation. The PNG was visually inspected and depicts the
Terran base and mining workers. This avoids BurnySC2's replay-path restriction to
the home Documents folder. ffmpeg is already installed. Export should happen
after training so rendering does not slow simulations.

Relevant primary sources:
- https://github.com/Blizzard/s2client-proto/blob/master/docs/linux.md
- https://github.com/Blizzard/s2client-proto/blob/master/docs/protocol.md

## Constraints

No sudo or large downloads. No deletion or relocation of sibling repositories,
old checkpoints, logs, replays, or game data. Work in `.worktrees/terran-rl` on
`Sam-v6/terran-rl`. Preserve examples and attribution. Change structure only where
needed for a usable package, commands, tests, and artifact management. Defer ladder
integration until computer-opponent training and evaluation work.

## Experiment boundaries

No build-order recipes hidden inside macro actions: worker production, supply,
production structures, unit choice, tech, expansion and attack/retreat timing are
policy choices. Resource/tech legality checks and construction placement are
execution primitives. Legal actions must include a wait action. Scripted worker
assignment and combat micro run at a separate cadence from macro decisions.

Use observed state changes and terminal wins/losses for reward; record individual
reward components. Avoid repeatedly rewarding an unchanged stockpile/army. Treat
game-time truncation distinctly from terminal defeat and bootstrap appropriately.
No policy update from engine crashes or callback errors. Evaluation always disables
exploration and learning and reports seeds, race, build, map and checkpoint identity.

Start with short smoke games, then complete training episodes, then compare policies
against Hard. Set finite episode/game-time/wall-time bounds. Review failures and
replay behavior before extending compute. A running process is not evidence of a
working learning update, and a single win is not evidence of reliable Hard strength.
