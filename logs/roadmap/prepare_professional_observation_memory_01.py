"""Select strictly causal observation pointers; never use past command labels."""
import bisect
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path('logs/roadmap')
PRO = ROOT / 'professional-production-choice-01'
OUT = ROOT / 'professional-observation-memory-01'
LAGS = (45, 112, 336)  # approximately 2, 5, 15 seconds at 22.4 loops/sec


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with gzip.open(path, 'rt') as stream:
        return [json.loads(line) for line in stream]


def main():
    report = json.loads((PRO / 'report.json').read_text())
    for path, digest in report['bindings'].items():
        assert sha(Path(path)) == digest, path
    OUT.mkdir(exist_ok=False)
    bindings = {str(PRO / 'report.json'): sha(PRO / 'report.json')}
    counts = {'teaching': 0, 'diagnostic': 0}
    missing = [0, 0, 0]
    frames = 0
    for game in report['games']:
        source = ROOT / 'human-command-cohort-02' / game['game'] / 'corpus/examples.jsonl.gz'
        targets = PRO / game['game'] / 'examples.jsonl.gz'
        assert report['bindings'][str(source)] == sha(source)
        source_rows = rows(source)
        ordered = sorted((row['observation']['game_loop'], i) for i, row in enumerate(source_rows))
        loops = [loop for loop, _ in ordered]
        selected = []
        for target in rows(targets):
            current_loop = target['observation']['game_loop']
            slots = []
            for index, lag in enumerate(LAGS):
                candidate = bisect.bisect_right(loops, current_loop - lag) - 1
                if candidate < 0:
                    slots.append(None)
                    missing[index] += 1
                    continue
                loop, row_index = ordered[candidate]
                assert loop <= current_loop - lag
                slots.append({'source_row': row_index, 'loop': loop, 'age_loops': current_loop - loop})
                frames += 1
            selected.append({'source_key': target['label']['source_key'], 'current_loop': current_loop, 'slots': slots})
        output = OUT / (game['game'] + '.json')
        output.write_text(json.dumps(selected) + '\n')
        counts[game['role']] += len(selected)
        for path in (source, targets, output):
            bindings[str(path)] = sha(path)
    assert counts == {'teaching': 1267, 'diagnostic': 289}
    result = {
        'status': 'prepared_causal_observation_pointers',
        'lags_loops': LAGS, 'loops_per_second': 22.4,
        'selection': 'Latest actual observation at or before current loop minus lag; ties choose last source row',
        'counts': counts, 'available_past_frames': frames, 'missing_slots': missing,
        'input_contract': 'Only source observation; strip recent_commands and command references before encoding. Include actual age and missing mask. No source labels, commands, player identity, or future observations as features.',
        'training': False, 'native_games': False, 'rl': False,
        'bindings': bindings,
    }
    (OUT / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'bindings'}))


if __name__ == '__main__':
    main()
