"""Recover source evidence for the native13 missing Factory; no label synthesis."""
import hashlib
import json
from pathlib import Path
import mpyq
from src.learning.replay_extract import load_protocol, replay_metadata
from src.learning.tournament_record import decode_record
root = Path('logs/roadmap'); out = root/'missing-factory-target-update-01'; out.mkdir(exist_ok=False)
replay = root/'pro-preconverted-probe-01/2cda222081e80d9a1c188698ce9bcda6.SC2Replay'
meta, _ = replay_metadata(replay); protocol = load_protocol(int(meta['BaseBuild'].removeprefix('Base')))
events = list(protocol.decode_replay_game_events(mpyq.MPQArchive(str(replay)).read_file('replay.game.events')))
source = [e for e in events if e.get('_userid', {}).get('m_userId') == 0]
command = next(e for e in source if e['_event'].endswith('.SCmdEvent') and e.get('m_sequence') == 636)
update = next(e for e in source if e['_event'].endswith('.SCmdUpdateTargetPointEvent') and e['_gameloop'] == 7171)
manager = next(e for e in source if e['_event'].endswith('.SCommandManagerStateEvent') and e['_gameloop'] == 7171)
assert command['m_abil'] == dict(m_abilLink=129, m_abilCmdIndex=10, m_abilCmdData=None)
assert [update['m_target'][axis]/4096 for axis in ('x', 'y')] == [134.5, 37.5]
assert manager['m_sequence'] == 637 and manager['m_state'] == 1
recordpath = root/'pro-preconverted-probe-01/fall-record-870.bin'
r = decode_record(recordpath.read_bytes()); f = r['units']['fields']; frames = []
for i, step in enumerate(r['units']['step']):
    if int(f['id'][i]) == 4392484873:
        frames.append(dict(loop=int(r['steps']['game_loop'][step]), kind=int(f['unitType'][i]),
                           point=list(map(float, f['pos'][i][:2])), progress=float(f['build_progress'][i])))
assert frames[0]['kind'] == 27 and frames[0]['point'] == [134.5, 37.5]
assert frames[0]['loop'] == 7262 and frames[0]['progress'] < .01
rawpath = root/'pro-preconverted-probe-01/raw-commands-870.json'
raw = json.loads(rawpath.read_text()); assert not any(e.get('m_sequence') == 637 for e in raw)
result = dict(status='verified_missing_source_target_update', command=command, target_update=update,
              manager=manager, source_factory_first_observation=frames[0], source_factory_tag=4392484873,
              omitted_from_raw_command_dump=True, training=False, rl=False,
              limitations=['This identifies missing event coverage; actor resolution and inherited-command semantics still need validation before adding a teaching label.'],
              bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),replay,recordpath,rawpath)})
(out/'audit.json').write_text(json.dumps(result, indent=2)+'\n');(out/'auditor.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(result))
