import os
from pathlib import Path


_PROJECT_ROOT = Path(__file__).resolve().parents[1]

SC2_VOID_BOT_HOME = str(_PROJECT_ROOT)
SC2_GAME_PATH = str(_PROJECT_ROOT.parent / "game" / "SC2.4.10" / "StarCraftII")

os.environ.setdefault("VOID_BOT_HOME", SC2_VOID_BOT_HOME)
os.environ.setdefault("SC2PATH", SC2_GAME_PATH)
