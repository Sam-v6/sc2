"""Classify production intent conservatively; never infer a quiet interval."""
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import mpyq

from src.learning.replay_extract import load_protocol, replay_metadata
from src.learning.tournament_commands import REGULAR_FLAGS

ROOT = Path('logs/roadmap/human-command-cohort-02')
SOURCE = Path('logs/roadmap/production-decisions-01')
OUT = Path('logs/roadmap/production-timing-audit-02')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ability_key(event):
    ability = event['m_abil']
    return None if ability is None else (ability['m_abilLink'], ability['m_abilCmdIndex'])


def main():
    verified = json.loads((SOURCE / 'verification.json').read_text())
    report = json.loads((SOURCE / 'report.json').read_text())
    for path, digest in report['bindings'].items():
        assert sha(path) == digest, path
    assert verified
    OUT.mkdir(exist_ok=False)
    bindings = {str(Path(__file__)): sha(__file__), str(SOURCE / 'verification.json'): sha(SOURCE / 'verification.json')}
    results = []
    for game in report['games']:
        parent = ROOT / game['game']
        job = json.loads((parent / 'job.json').read_text())
        receipt = json.loads((parent / 'corpus/dataset.json').read_text())
        user = receipt['player']['player_info'].get('user_id')
        recon = json.loads((parent / 'reconciliation.json').read_text())['games'][0]
        user = recon['source_user_id'] if user is None else user
        meta, _ = replay_metadata(job['replay'])
        protocol = load_protocol(int(meta['BaseBuild'].removeprefix('Base')))
        archive = mpyq.MPQArchive(job['replay'])
        source = {(e['_gameloop'], e['m_sequence']): e for e in protocol.decode_replay_game_events(archive.read_file('replay.game.events')) if e['_event'].endswith('.SCmdEvent') and e.get('_userid', {}).get('m_userId') == user}
        rows = list(map(json.loads, gzip.open(parent / 'corpus/examples.jsonl.gz', 'rt')))
        names = {a['ability_id']: a.get('friendly_name', '') for a in json.loads(Path(job['catalog']).read_text())['game_data']['abilities']}
        production = lambda a: names[a].startswith(('Build ', 'Train ', 'Research ')) or names[a] in ('Morph OrbitalCommand', 'Morph PlanetaryFortress')
        known = {(r['action_loop'], r['source_sequence']): r['commands'][0]['ability'] for r in rows}
        mapping = defaultdict(set)
        proofs = defaultdict(list)
        for key, native in known.items():
            if key in source:
                link = ability_key(source[key])
                mapping[link].add(native)
                proofs[link].append(key)
        windows = json.loads((SOURCE / game['game'] / 'windows.json').read_text())
        unknown = set(map(tuple, windows['unknown_keys']))
        events = {key: dict(key=key, classification='production' if production(a) else 'nonproduction', ability=a, proof='verified_command') for key, a in known.items()}
        for key in sorted(unknown):
            event = source.get(key)
            item = dict(key=key, classification='possible_production', proof='unresolved_protocol_context')
            if event is not None:
                link = ability_key(event)
                candidates = mapping.get(link, set())
                classes = {production(a) for a in candidates}
                flags = event['m_cmdFlags']
                if classes == {False}:
                    item.update(classification='nonproduction', proof='same_numeric_ability_as_verified_commands', reference_keys=proofs[link])
                elif classes == {True} and flags & 0x100 and not flags & ~REGULAR_FLAGS:
                    item.update(classification='production', proof='regular_user_command_same_numeric_production_ability', reference_keys=proofs[link], ability=next(iter(candidates)) if len(candidates) == 1 else None)
            events[key] = item
        labels = []
        phases = defaultdict(Counter)
        end = windows['source_loops'][-1]
        covered = 0
        for anchor in windows['windows']:
            loop = anchor['loop']
            interval = sorted((v for k, v in events.items() if loop <= k[0] < loop + 44), key=lambda e: e['key'])
            positives = [e for e in interval if e['classification'] == 'production']
            possible = [e for e in interval if e['classification'] == 'possible_production']
            act = True if positives else None if possible or loop + 44 > end else False
            first = positives[0] if positives else None
            identity = first['ability'] if first and first.get('ability') is not None and not any(e['key'] < first['key'] for e in possible) else None
            labels.append(dict(loop=loop, act=act, first_ability=identity, first_key=first['key'] if first else None, possible_keys=[e['key'] for e in possible]))
            phase = 'opening' if loop < 22.4 * 240 else 'middle' if loop < 22.4 * 600 else 'late'
            phases[phase][str(act)] += 1
            covered += max(0, min(44, end - loop))
        counts = Counter(str(e['act']) for e in labels)
        span = end - windows['source_loops'][0]
        result = dict(game=game['game'], role=game['role'], anchors=len(labels), counts=dict(counts), phases={k: dict(v) for k, v in phases.items()}, classified_unknown=dict(Counter(events[k]['classification'] for k in unknown)), covered_elapsed_loops=covered, total_elapsed_loops=span, coverage_fraction=covered / span, identity_examples=sum(e['first_ability'] is not None for e in labels))
        (OUT / (game['game'] + '.json')).write_text(json.dumps(dict(summary=result, labels=labels, events=list(events.values())), indent=2) + '\n')
        results.append(result)
        print(json.dumps(result), flush=True)
    for path, digest in report['bindings'].items():
        assert sha(path) == digest, path
    (OUT / 'report.json').write_text(json.dumps(dict(status='completed_conservative_source_classification', games=results, bindings={**report['bindings'], **bindings}, training=False, rl=False, limitations=['Unresolved manager events remain possible production.', 'Known production proves a positive even with earlier unknown events; first identity remains censored.', 'Numeric ability mappings are local to each game and supported by verified accepted commands.', 'Actual observation gaps remain uncovered; no interpolated states or inferred negatives.']), indent=2) + '\n')


if __name__ == '__main__':
    main()
