"""Plot resources from the SC2 replay exporter's actual game observations."""
import argparse
import os
from src.path import SC2_VOID_BOT_HOME
os.environ.setdefault("MPLCONFIGDIR", os.path.join(SC2_VOID_BOT_HOME, "logs", ".matplotlib"))
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def plot_telemetry(source, output):
    rows = json.loads(Path(source).read_text())['telemetry']
    if not rows:
        raise ValueError('No replay observations to plot')
    fig, axis = plt.subplots()
    for key in ('minerals', 'vespene'):
        axis.plot([row['game_time'] for row in rows], [row[key] for row in rows], label=key)
    axis.set_xlabel('Game time (seconds)')
    axis.set_ylabel('Resources')
    axis.legend()
    axis.grid(True)
    fig.tight_layout()
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('observations', type=Path, help='The video export .frames.json file')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    plot_telemetry(args.observations, args.output)


if __name__ == '__main__':
    main()
