import os
import json
import matplotlib.pyplot as plt
from s2protocol import versions
import mpyq

# Path to your SC2Replay file
replay_path = "/home/sam/repos/sc2-repos/sc2-void-bot/replays/zergling_rush_TorchesAIE_20250817_095707.SC2Replay"

# Load the MPQ archive
archive = mpyq.MPQArchive(replay_path)
contents = archive.extract()

# Identify the protocol version
header = json.loads(archive.read_file("replay.gamemetadata.json").decode("utf-8"))
base_build = int(header["BaseBuild"].replace("Base", ""))
protocol = versions.build(base_build)

# Load the game details
details = protocol.decode_replay_details(archive.read_file("replay.details"))
init_data = protocol.decode_replay_initdata(archive.read_file("replay.initData"))
game_events = protocol.decode_replay_game_events(archive.read_file("replay.game.events"))
tracker_events = protocol.decode_replay_tracker_events(archive.read_file("replay.tracker.events"))

# Get player names
players = {
    player['m_workingSetSlotId']: player['m_name'].decode('utf-8')
    for player in details['m_playerList']
}

# Init resource tracking
resource_data = {name: {"time": [], "minerals": [], "vespene": []} for name in players.values()}

# Extract from tracker events
for event in tracker_events:
    if event.get('_event') == 'PlayerStatsEvent':
        pid = event.get('player_id')
        name = players.get(pid)
        if name is None:
            continue  # Player ID mismatch

        gametime = event['_gameloop'] / 22.4
        resource_data[name]["time"].append(gametime)
        resource_data[name]["minerals"].append(event["minerals_current"])
        resource_data[name]["vespene"].append(event["vespene_current"])


# Plot
for name, data in resource_data.items():
    plt.plot(data["time"], data["minerals"], label=f"{name} - Minerals")
    plt.plot(data["time"], data["vespene"], label=f"{name} - Vespene", linestyle="--")

plt.xlabel("Time (s)")
plt.ylabel("Resources")
plt.title("Minerals & Vespene Over Time")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("resources_over_time.png")
