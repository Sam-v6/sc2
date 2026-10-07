"""Run the label audit on the already verified diagnostic, before cohort fitting."""
import importlib.util,json,hashlib
from pathlib import Path
ROOT=Path('logs/roadmap');pilot=ROOT/'native-timing-pilot-source-02';pilot.mkdir(exist_ok=False)
manifest=json.loads((ROOT/'dense-timing-cohort-01/manifest.json').read_text());game=next(g for g in manifest['games'] if g['game']=='51482')
verification=json.loads((ROOT/'human-rom-dense-01/verification.json').read_text());assert verification['status']=='verified_dense_cadence_native_action_preservation_and_current_fog'
manifest=dict(games=[game],scope='singleton reused diagnostic label audit',bindings=verification['bindings'])
(pilot/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
bindings={**verification['bindings'],str(Path(__file__)):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(pilot/'report.json').write_text(json.dumps(dict(status='completed_dense_native_cohort',scope='singleton already verified diagnostic; no new extraction',bindings=bindings),indent=2)+'\n')
spec=importlib.util.spec_from_file_location('native_timing_audit',ROOT/'prepare_native_timing_02.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.ROOT=pilot;module.OUT=ROOT/'native-production-timing-pilot-02';module.main()
