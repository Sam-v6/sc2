"""Reconstruct native production from original replays and trace accounting."""
import base64
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
import mpyq
from src.learning.production_outcomes import production_outcomes
from src.learning.replay_extract import load_protocol, replay_metadata

OUT = Path('logs/roadmap/primitives-native-02/panel')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    report = json.loads((OUT/'report.json').read_text())
    contract = json.loads((OUT/'contract.json').read_text())
    assert report['status'] == 'completed' and len(report['results']) == 6
    assert not report['training'] and not report['rl']
    for p, checksum in report['bindings'].items():
        assert sha(p) == checksum, p
    bindings = {str(p): sha(p) for p in (OUT/'report.json', OUT/'contract.json', Path(__file__))}
    results = []
    for job, receipt in zip(contract['jobs'], report['results'], strict=True):
        assert receipt['job'] == job
        replay = Path(job['replay'])
        trace = replay.with_suffix('.primitives.jsonl.gz')
        data = replay.with_suffix('.primitives.data.json')
        assert replay.stat().st_size == receipt['replay_bytes']
        static = json.loads(data.read_text())
        descriptors = {u['unit_id']: u for u in static['units']}
        types = {u['name'] for u in static['units'] if u.get('race') == 1}
        macro_frames = raw_errors = delayed_errors = workers = army = 0
        attack_points = tank_sieges = 0
        last_score = None
        for line in gzip.open(trace, 'rt'):
            row = json.loads(line)
            assert len(row['commands']) == len(row['results'])
            raw_errors += sum(c != 1 for c in row['results'])
            delayed_errors += len(row['delayed_errors'])
            attack_points += sum(c['ability'] == 23 and c['target_point'] is not None for c in row['commands'])
            tank_sieges += sum(c['ability'] == 388 for c in row['commands'])
            state = row['observation']
            if state is None:
                continue
            macro_frames += 1
            visibility = state['map']['visibility']
            pixels = base64.b64decode(visibility['data'])
            for enemy in state['units']:
                if enemy['alliance'] == 4:
                    x, y = [round(v) for v in enemy['position'][:2]]
                    assert pixels[y*visibility['width']+x] == 2
            own = [u for u in state['units'] if u['alliance'] == 1]
            workers = max(workers, sum(u['unit_type'] == 45 for u in own))
            army = max(army, sum(u['unit_type'] in (48, 33, 32) for u in own))
            for command in row['commands']:
                if command['ability'] == 23 and command['target_unit'] is not None:
                    target = next(u for u in state['units'] if u['tag'] == command['target_unit'])
                    assert target['alliance'] == 4 and target['display_type'] == 1
                    for tag in command['units']:
                        actor = next(u for u in own if u['tag'] == tag)
                        assert any(w['type'] in (3, 2 if target.get('is_flying') else 1)
                                   for w in descriptors[actor['unit_type']].get('weapons', []))
            last_score = row['score']
        assert raw_errors == receipt['primitives']['raw_action_errors']
        assert delayed_errors == receipt['primitives']['delayed_action_errors']
        meta, _ = replay_metadata(replay)
        archive = mpyq.MPQArchive(str(replay))
        protocol = load_protocol(int(meta['BaseBuild'][4:]))
        details = protocol.decode_replay_details(archive.read_file('replay.details'))
        actual_result = details['m_playerList'][0]['m_result']
        if receipt['result'] in ('Victory', 'Defeat'):
            assert actual_result == (1 if receipt['result'] == 'Victory' else 2)
        events = list(protocol.decode_replay_tracker_events(archive.read_file('replay.tracker.events')))
        outcomes = production_outcomes(events, 1, types, {'OrbitalCommand', 'PlanetaryFortress'},
                                       {u['name'] for u in static['upgrades']})
        actual = Counter(n for _, n in outcomes)
        header = protocol.decode_replay_header(archive.header['user_data_header']['content'])
        item = dict(race=job['race'], build=job['build'], seed=job['seed'], result=receipt['result'],
                    opponent_replay_name=details['m_playerList'][1]['m_name'].decode(),
                    requested_difficulty='Hard (protocol value 5)', seconds=header['m_elapsedGameLoops']/22.4,
                    sampled_worker_peak=workers, sampled_army_peak=army, actual_production=dict(actual),
                    macro_frames=macro_frames, raw_action_errors=raw_errors, delayed_action_errors=delayed_errors,
                    point_attack_commands=attack_points, siege_commands=tank_sieges,
                    collected_minerals=last_score['collected_minerals'],
                    killed_unit_value=last_score['killed_value_units'], killed_structure_value=last_score['killed_value_structures'])
        results.append(item)
        print(json.dumps(item), flush=True)
        bindings.update({str(p): sha(p) for p in (replay, trace, data)})
    result = dict(status='verified_development', controller='scripted', training=False, rl=False,
                  wins=sum(r['result'] == 'Victory' for r in results), games=results,
                  peak_cpu=report['peak_cpu'], bindings=bindings,
                  limits=['Six development games are not the 30-game acceptance panel.',
                          'Fog and weapon-compatibility checks cover sampled macro frames; replay outcomes cover full games.',
                          'Army peaks exclude Medivacs; sampled peaks can miss between-sample births.'])
    (OUT/'verification.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()
