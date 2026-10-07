import json
from pathlib import Path
from src.learning.gameplay import Command, protocol_dict
from src.learning.replay_extract import main

original = Command.from_proto.__func__

def traced(cls, action):
    try:
        return original(cls, action)
    except ValueError:
        Path('logs/roadmap/replay-51959-unsupported-action-01.json').write_text(
            json.dumps(protocol_dict(action), indent=2) + '\n'
        )
        raise

Command.from_proto = classmethod(traced)
if __name__ == '__main__':
    main()
