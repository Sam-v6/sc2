# SC2 Imports
from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race
from sc2.main import run_game
from sc2.player import Bot, Computer

# Base imports
import os
from datetime import datetime
import argparse
import multiprocessing as mp
from queue import Empty
from concurrent.futures import ThreadPoolExecutor, as_completed

# Additional imports
import pandas as pd
import numpy as np

# Local imports
from bots.warpgate_push import WarpGateBot
from bots.proxy_rax import ProxyRaxBot
from bots.mass_reaper import MassReaperBot
from bots.one_base_battlecruiser import BCRushBot
from bots.zerg_rush import ZergRushBot
from path import SC2_VOID_BOT_HOME, SC2_GAME_PATH


TIMEOUT = (60*5)  # seconds

def run_single_game(bot_class_name, bot_race, strat_name, opponent_race, difficulty, map_name, dev):
    bot_instance = Bot(bot_race, bot_class_name())

    if dev:
        os.environ["DEV"] = "1"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    replay_name = f"{strat_name}_{map_name}_{timestamp}.SC2Replay"
    replay_path = os.path.join(SC2_VOID_BOT_HOME, "replays", replay_name)

    try:
        print(f'Running {strat_name} on {map_name} vs {opponent_race}-{difficulty}...')
        result = run_game(
            maps.get(map_name),
            [bot_instance, Computer(opponent_race, difficulty)],
            realtime=False,
            save_replay_as=replay_path,
        )
        return (strat_name, opponent_race, difficulty, map_name, result.name)
    except Exception as e:
        print(f"Error running {strat_name} on {map_name}: {e}")
        return (strat_name, opponent_race, difficulty, map_name, "ERROR")

def _child(q, job):
    """
    Runs the actual child job with some exception handling
    """
    bot_class, bot_race, strat_name, opponent_race, difficulty, map_name, dev = job
    try:
        res = run_single_game(bot_class, bot_race, strat_name, opponent_race, difficulty, map_name, dev)
        # res is already a 5-tuple in both success and error paths above
        q.put(res)
    except Exception as e:
        q.put((strat_name, opponent_race, difficulty, map_name, f"EXCEPTION:{e!r}"))

def run_with_hard_timeout(job, seconds=TIMEOUT):
    """
    This fcn serves as the lightweight thread supervisor/ochestrator that spawns a child process which runs a game. If this process exceeds a timeout, the process will be killed
    """
    ctx = mp.get_context("spawn")
    q = ctx.Queue()
    p = ctx.Process(target=_child, args=(q, job), daemon=False)
    p.start()
    p.join(seconds)

    bot_class, bot_race, strat_name, opponent_race, difficulty, map_name, dev = job

    # Will try to terminate gracefully, if that doesn't work then we will hard kill it
    if p.is_alive():
        try:
            p.terminate()
            p.join(1.0)
            if p.is_alive():
                # Escalate if still stubborn
                p.kill()
                p.join(0.5)
        finally:
            pass
        return (strat_name, opponent_race, difficulty, map_name, "TIMEOUT")

    try:
        res = q.get(timeout=1.0)
        return res if isinstance(res, tuple) and len(res) == 5 else \
               (strat_name, opponent_race, difficulty, map_name, f"BAD_RESULT:{res!r}")
    except Empty:
        return (strat_name, opponent_race, difficulty, map_name, "NO_RESULT")

if __name__ == "__main__":

    ##############################################################
    # Setup
    ##############################################################
    # Get the args
    # --dev will enable logging and replays
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", action="store_true", help="Run in dev mode (no logging)")
    args = parser.parse_args()

    # Create the log and replay dirs
    os.makedirs(os.path.join(SC2_VOID_BOT_HOME, "logs"), exist_ok=True)
    os.makedirs(os.path.join(SC2_VOID_BOT_HOME, "replays"), exist_ok=True)

    # List of bots (bot class, race, name)
    bots = [
        (WarpGateBot, Race.Protoss, "warpgate_push"),
        # (ProxyRaxBot, Race.Terran, "proxy_rax"),
        # (MassReaperBot, Race.Terran, "reaper_rush"),
        # (BCRushBot, Race.Terran, "bc_rush"),
        # (ZergRushBot, Race.Zerg, "zergling_rush"),
    ]

    # Races
    races = [Race.Terran, Race.Protoss, Race.Zerg]

    # Difficulty
    difficulties = [
        Difficulty.VeryEasy,
        # Difficulty.Easy,
        # Difficulty.Medium,
        # Difficulty.MediumHard,
        # Difficulty.Hard,
        # Difficulty.Harder,
        # Difficulty.VeryHard
        ]

    # Simple
    bots = [
        (ZergRushBot, Race.Zerg, "zergling_rush"),
    ]

    # Races
    races = [Race.Terran]

    # Difficulty
    difficulties = [
        Difficulty.VeryHard
        ]

    # Get map list
    ladder_maps = []
    map_path = os.path.join(SC2_GAME_PATH, "Maps", "2025S2Maps")
    for f in os.listdir(map_path):
        if f.endswith(".SC2Map"):
            ladder_maps.append(f.split(".")[0])

    # Prepare job list (each is a tuple of inputs to `run_single_game`)
    jobs = []
    for bot_class, bot_race, strat_name in bots:
        for opponent_race in races:
            for difficulty in difficulties:
                for map_name in ladder_maps:
                    jobs.append((bot_class, bot_race, strat_name, opponent_race, difficulty, map_name, args.dev))

    ##############################################################
    # Multiprocessing
    ##############################################################
    cpus = max(1, os.cpu_count()//2)

    # This general approach works by:
    # -> Having 16 threads that work as lightweight supervisors, for each thread
    # ---> Spawns a child process that runs a single SC2 game (in our job list)
    # In a basic pool setup we cant have a timeout error but it will still allow jobs to run in the background until whole pool times out, in this setup we can actually kill discrete games that have exceeded our timeout, basically more efficient
    results = []
    try:
        with ThreadPoolExecutor(max_workers=cpus) as ex:
            futures = [ex.submit(run_with_hard_timeout, job, TIMEOUT) for job in jobs]
            for fut in as_completed(futures):
                results.append(fut.result())
    except KeyboardInterrupt:
        # Stop accepting new work and try to cancel what we can
        # (futures still running will be handled by process timeouts)
        pass
    finally:
        # Always persist what we have
        df = pd.DataFrame(results, columns=['bot_strategy','opponent_race','difficulty','map','result'])
        out = os.path.join(SC2_VOID_BOT_HOME, "logs", "master_results.csv")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        df.to_csv(out, index=False)
