import os
import subprocess
from pathlib import Path


_PROJECT_ROOT = Path(__file__).resolve().parents[1]

def resolve_sc2_path():
    if os.environ.get("SC2PATH"):
        return Path(os.environ["SC2PATH"]).expanduser().resolve()
    git = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=_PROJECT_ROOT, capture_output=True, text=True, check=False,
    )
    original_root = Path(git.stdout.strip()).parent if git.returncode == 0 else _PROJECT_ROOT
    return original_root.parent / "game" / "SC2.4.10" / "StarCraftII"


SC2_VOID_BOT_HOME = str(_PROJECT_ROOT)
SC2_GAME_PATH = str(resolve_sc2_path())

os.environ.setdefault("VOID_BOT_HOME", SC2_VOID_BOT_HOME)
os.environ.setdefault("SC2PATH", SC2_GAME_PATH)
