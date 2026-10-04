# SC2 Void Bot

Headless StarCraft II computer-opponent experiments on Linux. The current scripted
bots are baselines. The Terran macro learner is an explicit first experiment;
its observation/action representation is not the project's final design.

## Setup

Python 3.12 and uv are used locally. Install the locked Python dependencies:

```bash
uv sync --frozen
uv run python -m unittest discover -s tests -v
```

No game installation is downloaded by these commands. By default the code finds the
existing sibling `../game/SC2.4.10/StarCraftII`, including from a Git worktree. For
another installation, set the path before running:

```bash
export SC2PATH=/absolute/path/to/StarCraftII
```

The game directory must contain `Versions` and `Maps`. Local Linux experiments use
SC2 4.10, build 75689. Maps and the replay's game build must match for playback.

## Scripted comparisons

Run from the repository/worktree root:

```bash
uv run python -m src.runner --bot reaper --race Zerg --difficulty Hard --map Simple64 --games 1 --workers 1 --game-seconds 60 --dev --output logs/smoke
uv run python -m src.runner --bot reaper --race Terran --build Rush --difficulty Hard --map Simple64 --games 4 --workers 4 --seed 100 --output logs/comparison
```

`python src/runner.py` is also supported. `--help` lists available bots and options.
Defaults are non-realtime simulation, step 8, four workers, a 1,200-game-second
limit and a 300-wall-second limit. Each game has a unique replay and JSON receipt.
A cutoff Tie is recorded as `truncated`; worker failures/timeouts are separate
statuses and make the command exit nonzero. The supervisor cleans only its own
worker's process group, including game descendants.

`--dev` records score telemetry in Parquet under `logs/`. Logging buffers rows and
converts them once at game end. These are our bot's observations, not omniscient
opponent statistics. For old telemetry plots:

```bash
uv run python -m src.processing.plotter
```

## Layout and preserved references

- `src/runner.py`, `src/runtime.py`, `src/path.py`: commands, supervision, installation discovery.
- `src/bots/`, `src/examples/`: existing scripted strategies/examples, with original attribution.
- `src/common/`: score telemetry base class.
- `src/processing/`: analysis and replay tools.
- `tests/`: standard-library unittest tests; no extra test framework is required.
- `logs/`, `replays/`: ignored run artifacts; keep them outside Git.
- `docs/legacy/`: preserved old resource plot and score-column snapshot.
- `docs/performance-baseline.md`: measurements, including three scripted losses against Hard.
- `docs/terran-rl-experiment.md`: intended experiment and acceptance evidence.

The sibling `SC2RL` is a separate Protoss PPO tutorial with old models and logs.
`pysc2` and `sharpy-starter-bot` are separate reference projects. None is required
by this runner. The sibling `environment.sh` and `requirements.txt` are legacy
setup files; this project uses SC2PATH discovery, pyproject.toml and uv.lock.
They, game data, old models and replays have been preserved.

## Replay proof and remaining work

The audit successfully replayed a saved game using the installed OSMesa library
and exported RGB frames to an MP4 using the already-installed ffmpeg. The diagnostic
video and receipts live in the implementation worktree's `logs/audit/`.
Reusable training and replay-export commands are below.
The scripted-bot examples do not establish learned strength. A frozen experimental
policy has now won one of six development Hard games; see the experiment report.

## Terran learning experiment

The NumPy Double-DQN consumes live economy, production, army, and visible-enemy features.
It chooses atomic build/train/tech/expand/attack/retreat actions. There is no scripted
build order or fixed army mix. Gathering, placement, depot lowering, MULE execution,
defense and combat execution are primitives. The first feature representation is
limited; spatial observations and broader actions remain future experiments.

```bash
uv run python -m src.rl.train --episodes 2 --workers 4 --macro-seconds 1 --game-seconds 120 --checkpoint logs/my-run/policy.npz --output logs/my-run
uv run python -m src.rl.train --episodes 20 --workers 4 --checkpoint logs/my-run/policy.npz --output logs/my-run
uv run python -m src.rl.train --mode evaluate --episodes 30 --seed 50000 --builds Rush Timing Power Macro Air --checkpoint logs/my-run/frozen.npz --output logs/my-evaluation
```

For evaluation, first copy the desired checkpoint to `frozen.npz` and retain that
snapshot. Training resumes an existing checkpoint including network/target weights,
optimizer, experience, RNG and episode count. A separate attempt cursor advances training seeds/opponents on
resume, including mixed-success batches; evaluation defaults to seeds starting at 10000. Use a new seed bank for final
acceptance after inspecting development evaluations. `--maps`, `--races`, `--builds`
and `--difficulty` select computer opponents; `--macro-seconds` controls decision
cadence. Army distance from home/enemy spawn and time since the last stance change
help distinguish movement even when enemies are hidden. Resume infers the stored cadence and rejects a changed training cadence.
Legacy checkpoints lacking this metadata require their known original
`--legacy-macro-seconds` value. New runs default to five seconds; the one-second
experiment above gives the atomic actions more production opportunities. Each macro action attempts one operation, so slower cadence also limits
production throughput. Do not run multiple trainers against the same checkpoint.

Actions are legal at the observed resource/tech level. A logged `executed` value
means a command was issued successfully by the Python client; SC2 may still reject
it or construction may subsequently fail. Inspect replay/state changes to establish
actual completion. The logs contain chosen actions, legal masks, snapshots and reward
components. The current capacity potential uses .5 per worker, .2 per army supply and 2 per
base, capped by the observation encoder. Spending resources alone earns no reward;
terminal wins/losses receive +100/-100. Checkpoints identify their reward objective,
and incompatible or unknown objectives are rejected for training resume.
Replay learning uses up to 32 macro rewards with the actual bootstrap discount,
stopping before a later nongreedy action from the frozen worker policy. New-checkpoint discounting accounts for macro cadence. Time-limit ties bootstrap instead of being labeled defeats.

Four workers collect games from a shared frozen behavior checkpoint by default.
The parent merges successful games in launch order and learns from their experience;
worker weights and optimizer state never replace the parent. Set `--workers 1` for
serial collection. A clean interruption stops owned game workers and preserves the
last promoted checkpoint.

Each game writes a replay, JSON receipt and JSONL decisions. Receipts identify source
and map hashes, game build, action RNG seed and behavior checkpoint hash. Failed/timed-out games
do not promote a candidate checkpoint. Training updates occur in the parent only after successful
game execution; frozen evaluation performs no updates and checks the checkpoint hash.
A smoke-test update is not evidence of a strong policy. The initial batches failed against Hard. An economic-potential probe subsequently
won one of six frozen Hard games against Protoss Rush; a separate capacity probe
won one of six against Terran Macro. Broader economic-probe evaluation won only
one of thirty games. These are preliminary results;
see [the experiment report](docs/experiment-results.md) for progress.

## PPO comparison using the existing Torch runtime

The default learner remains DQN. A separate PPO experiment reuses Torch already
installed in the sibling SC2RL environment, without installing it in game workers:

```bash
uv run python -m src.rl.train --algorithm ppo --torch-python /home/sam/repos/sc2-repos/SC2RL/.venv/bin/python --macro-seconds 1 --episodes 4 --game-seconds 180 --difficulty VeryEasy --checkpoint logs/my-ppo/policy.npz --output logs/my-ppo
uv run python -m src.rl.train --torch-python /home/sam/repos/sc2-repos/SC2RL/.venv/bin/python --episodes 20 --difficulty VeryEasy --checkpoint logs/my-ppo/policy.npz --output logs/my-ppo
```

Keep the virtualenv interpreter path; resolving its symlink bypasses that
environment. The helper disables bytecode writes and leaves the sibling runtime
unchanged. Saved models infer and validate their algorithm. PPO uses a masked
categorical actor and value head, normalized capacity rewards (.01 scale), GAE,
and one clipped update over each batch's valid complete game trajectories.
Rollouts are discarded after updating; they are not DQN replay experience.

Game workers and frozen inference use NumPy. Only CPU gradient updates launch the
existing Torch interpreter. Receipts identify the backend/version, source, shared
rollout batch and update count. Helper failures/timeouts preserve the canonical
checkpoint. Frozen evaluation uses greedy actor choices and requires no Torch
backend; successful smoke updates do not establish Hard strength.

## Watch a saved replay on Linux

The installed OSMesa library and ffmpeg are sufficient here; no VM is needed for MP4
viewing. Export after training so rendering does not consume simulation resources:

```bash
uv run python -m src.processing.replay_video /absolute/path/game.SC2Replay --map-file /absolute/path/to/Simple64.SC2Map --output logs/game.mp4 --camera overview --step 22 --fps 4
uv run python -m src.processing.replay_plotter logs/game.frames.json --output logs/game-resources.png
```

Choose `--camera base` for a closer view, `--player 2` for the computer's perspective,
and `--omniscient` to remove fog during replay viewing only. `--max-frames` and
`--wall-seconds` bound export; the receipt declares when the frame limit was reached.
At step 22 and 4 fps the video runs about 3.9 times game speed. Defaults (step 3,
8 fps) approximate normal speed. Supply `--library` for another installed OSMesa path.
The exporter checks the replay's exact SC2 build and fails if it is unavailable.
It streams RGB frames to ffmpeg and saves per-frame resource observations for plots.

MP4 is portable viewing, not an interactive SC2 client. For interactive Windows
playback, retain the original replay and matching map, install SC2 with access to
that replay's build (these local runs require 4.10/build 75689), copy the map to its
Maps directory, copy the replay to Documents/StarCraft II/Replays, and open it from
the game's replay browser. A current client without the old build/map data may
fail. This Windows route has not been verified on a Windows machine; Linux MP4 export
has been verified locally.
