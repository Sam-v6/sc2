"""Offline audit: failed attempts consume the shared authorization reservation."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

BASE = Path(__file__).resolve().parent
runner = BASE / 'recover_assetsproduct.py'
spec = importlib.util.spec_from_file_location('recovery', runner)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
results = []
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    probe = root / 'logs/roadmap/probe'
    probe.mkdir(parents=True)
    source = root / 'src/learning/casc_asset.py'
    source.parent.mkdir(parents=True)
    source.write_bytes((BASE.parents[2] / 'src/learning/casc_asset.py').read_bytes())
    plan = {'proposed_maximum_download_bytes':20, 'encrypted_stream_start':100,
            'source':'https://invalid.example/archive.zip', 'record_offset':0,
            'record_bytes':1, 'encoded_key':'0'*32, 'native_content_key':'0'*32}
    (probe/'required-assetsproduct-download-plan-01.json').write_text(json.dumps(plan))
    module.BASE = probe
    # Simulate interruption after an HTTP request starts. No network is used.
    with patch.object(module.urllib.request, 'urlopen', side_effect=KeyboardInterrupt('mock interruption')) as http:
        for number, expected in [(1, KeyboardInterrupt), (2, ValueError)]:
            output = root / f'attempt-{number}'
            with patch('sys.argv', ['recovery', '--output', str(output), '--download']):
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        module.main()
                except expected:
                    pass
                else:
                    raise AssertionError('Expected interrupted/exhausted failure')
            receipt = json.loads((output/'receipt.json').read_text())
            ledger = json.loads((probe/'assetsproduct-prefix-ranges/download-budget.json').read_text())
            assert ledger['reserved_bytes'] == 20
            assert receipt['status'] == 'failed'
            assert receipt['reserved_network_bytes_cumulative'] == 20
            assert http.call_count == 1
            results.append({'attempt':number,'error':receipt['error_type'],
                            'reserved_bytes':ledger['reserved_bytes'],'mock_http_calls':http.call_count})
    offline = root/'offline'
    with patch.object(module.urllib.request, 'urlopen') as http:
        with patch('sys.argv', ['recovery', '--output', str(offline)]):
            try:
                module.main()
            except FileNotFoundError:
                pass
            else:
                raise AssertionError('Expected offline refusal')
        assert http.call_count == 0
        receipt = json.loads((offline/'receipt.json').read_text())
        assert receipt['download_enabled'] is False
        results.append({'offline_refused':True,'mock_http_calls':0})
report = {'runner_sha256':hashlib.sha256(runner.read_bytes()).hexdigest(),
          'audit_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'network_bytes':0,'mocked':True,'checks':results}
(BASE/'recovery-budget-audit-01.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
