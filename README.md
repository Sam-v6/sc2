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
No learned Hard-opponent win is claimed by the scripted-bot examples.

## Terran learning experiment

The NumPy Double-DQN consumes live economy, production, army, and visible-enemy features.
It chooses atomic build/train/tech/expand/attack/retreat actions. There is no scripted
build order or fixed army mix. Gathering, placement, depot lowering, MULE execution,
defense and combat execution are primitives. The first feature representation is
limited; spatial observations and broader actions remain future experiments.

```bash
uv run python -m src.rl.train --episodes 2 --game-seconds 120 --checkpoint logs/my-run/policy.npz --output logs/my-run
uv run python -m src.rl.train --episodes 20 --checkpoint logs/my-run/policy.npz --output logs/my-run
uv run python -m src.rl.train --mode evaluate --episodes 30 --seed 50000 --builds Rush Timing Power Macro Air --checkpoint logs/my-run/frozen.npz --output logs/my-evaluation
```

For evaluation, first copy the desired checkpoint to `frozen.npz` and retain that
snapshot. Training resumes an existing checkpoint including network/target weights,
optimizer, experience, RNG and episode count. Defaults advance training seeds on
resume; evaluation defaults to seeds starting at 10000. Use a new seed bank for final
acceptance after inspecting development evaluations. `--maps`, `--races`, `--builds`
and `--difficulty` select computer opponents; `--macro-seconds` controls decision
cadence. Each macro action attempts one operation, so slower cadence also limits
production throughput. Do not run multiple trainers against the same checkpoint.

Actions are legal at the observed resource/tech level. A logged `executed` value
means a command was issued successfully by the Python client; SC2 may still reject
it or construction may subsequently fail. Inspect replay/state changes to establish
actual completion. The logs contain chosen actions, legal masks, snapshots and reward
components. Potential shaping rewards state changes; terminal wins/losses receive
+100/-100. Replay learning uses up to 32 macro rewards with the actual bootstrap
discount. New-checkpoint discounting accounts for macro cadence. Time-limit ties bootstrap instead of being labeled defeats.

Each game writes a replay, JSON receipt and JSONL decisions. Failed/timed-out games
do not promote a candidate checkpoint. Training updates occur only after successful
game execution; frozen evaluation performs no updates and checks the checkpoint hash.
A smoke-test update is not evidence of a strong policy. The first full batch of twenty
Hard training games produced zero wins; see [the experiment report](docs/experiment-results.md) for progress.

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
