# SC2 Void Bot

Headless StarCraft II computer-opponent experiments on Linux. The current scripted
bots are baselines. The planned Terran macro learner is an explicit first experiment;
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
A reusable replay-export CLI and the Terran learning loop are under implementation.
No learned Hard-opponent win is claimed by the scripted-bot examples.
