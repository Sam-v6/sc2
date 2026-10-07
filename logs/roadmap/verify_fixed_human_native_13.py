"""Verify terminal diagnostic traces, provenance, and actual Factory attachment."""
import gzip
import hashlib
import json
from pathlib import Path
import mpyq
from src.learning.replay_extract import load_protocol, replay_metadata
root = Path('logs/roadmap')
checks = []
for number in (12, 13):
    out = root/f'fixed-human-plan-native-{number:02d}'
    contract = json.loads((out/'contract.json').read_text())
    report = json.loads((out/'report.json').read_text())
    episode = json.loads((out/'episode/episode.json').read_text())
    assert report['status'] == 'completed' and report['peak_cpu'] <= 80
    for p, sha in contract['bindings'].items():
        path = Path(p); rel = path.relative_to(Path.cwd()) if path.is_absolute() else path
        if path.suffix in ('.py', '.json'):
            path = out/'source-snapshot'/rel
        assert hashlib.sha256(path.read_bytes()).hexdigest() == sha, path
    rows = [json.loads(line) for line in gzip.open(out/'episode/trace.jsonl.gz', 'rt')]
    assert len(rows) == episode['frames'] > 0
    assert rows[-1]['loop'] == episode['divergence']['loop'] <= 13440
    assert not any(r['observation']['action_errors'] for r in rows)
    land = next(h for h in episode['history'] if h.get('ticket') == 119)
    assert land['result'] == 1 and land['command']['target_point'] == [131.5, 44.5]
    tag = land['command']['units'][0]
    attached = []
    for row in rows:
        units = row['observation']['units']
        actor = next((u for u in units if u['tag'] == tag), None)
        if actor and actor['unit_type'] == 27 and not actor.get('is_flying') and actor.get('add_on_tag'):
            addon = next(u for u in units if u['tag'] == actor['add_on_tag'])
            assert actor['position'][:2] == [131.5, 44.5]
            assert addon['position'][:2] == [134, 44]
            attached.append(row['loop'])
    assert attached
    replay = out/'episode/game.SC2Replay'; meta, _ = replay_metadata(replay)
    protocol = load_protocol(int(meta['BaseBuild'].removeprefix('Base')))
    init = protocol.decode_replay_initdata(mpyq.MPQArchive(str(replay)).read_file('replay.initData'))
    assert init['m_syncLobbyState']['m_userInitialData'][0]['m_randomSeed'] == 817501
    retired = [h for h in episode['history'] if h.get('event') == 'superseded_unsubmitted_build']
    if number == 13:
        assert len(retired) == 1 and retired[0]['ticket'] == 115 and retired[0]['replacement_ticket'] == 116
        assert episode['divergence']['reason'] == 'source_actor_unbound_or_lost'
    else:
        assert not retired and episode['divergence']['reason'] == 'source_foundation_identity_unresolved'
    result = dict(status='verified_terminal_diagnostic', native=number, frames=len(rows),
                  resolved_instructions=episode['instructions_resolved'], action_errors=0,
                  actual_factory_attachment_first_loop=min(attached),
                  failure=episode['divergence'], peak_cpu=report['peak_cpu'],
                  forced_leave=True, training=False, rl=False, learned_strength=False,
                  replay_sha256=hashlib.sha256(replay.read_bytes()).hexdigest())
    (out/'verification.json').write_text(json.dumps(result, indent=2)+'\n')
    (out/'source-snapshot/verifier.py').write_bytes(Path(__file__).read_bytes())
    checks.append(result)
print(json.dumps(checks))
