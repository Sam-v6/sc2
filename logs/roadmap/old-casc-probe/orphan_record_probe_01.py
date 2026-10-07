"""Read-only bounded-buffer scan for an exact record omitted from local indexes."""
import hashlib
import json
from pathlib import Path
import time

from src.learning.casc_asset import verify_record

base = Path('/home/sam/repos/sc2-repos/game/SC2.4.10/StarCraftII/SC2Data/data')
out = Path('logs/roadmap/old-casc-probe/orphan-record-01')
out.mkdir(exist_ok=False)
key = '31271d461c33eda86a4723e3cbdd8038'
needle = bytes.fromhex(key)[::-1]
files = sorted(base.glob('data.*'))
before = {str(p): {'bytes': p.stat().st_size, 'mtime_ns': p.stat().st_mtime_ns} for p in files}
start = time.monotonic()
read_bytes = 0
candidates = []
verified = []
for path in files:
    with path.open('rb') as stream:
        offset = 0
        tail = b''
        while True:
            assert time.monotonic() - start < 120
            block = stream.read(32 * 1024**2)
            if not block:
                break
            read_bytes += len(block)
            data = tail + block
            position = data.find(needle)
            while position >= 0:
                location = offset - len(tail) + position
                # Dedicated descriptor preserves the sequential scan position.
                with path.open('rb') as record_stream:
                    record_stream.seek(location)
                    header = record_stream.read(38)
                    if len(header) == 38 and header[30:34] == b'BLTE':
                        size = int.from_bytes(header[16:20], 'little')
                        assert 0 < size <= 250 * 1024**2
                        record_stream.seek(location)
                        record = record_stream.read(size)
                        decoded = verify_record(record, key, '1566ae22ab93ec0f9e246c9efbc7fec4', 264581)
                        (out / f'{path.name}-{location}.record').write_bytes(record)
                        (out / f'{path.name}-{location}.decoded').write_bytes(decoded)
                        verified.append({'path': str(path), 'offset': location, 'bytes': size, 'record_sha256': hashlib.sha256(record).hexdigest(), 'decoded_sha256': hashlib.sha256(decoded).hexdigest()})
                candidates.append({'path': str(path), 'offset': location})
                position = data.find(needle, position + 1)
            tail = data[-15:]
            offset += len(block)
    print(json.dumps({'scanned': str(path), 'read_bytes': read_bytes}), flush=True)
assert before == {str(p): {'bytes': p.stat().st_size, 'mtime_ns': p.stat().st_mtime_ns} for p in files}
report = {'status': 'exact_record_recovered' if verified else 'exact_record_not_present', 'scope': 'Exact reversed EKey header scan of all four installed physical archives; no original writes, network or substitute version content.', 'before_after_archive_stats': before, 'scan_bytes': read_bytes, 'buffer_bytes': 32 * 1024**2, 'candidates': candidates, 'verified_records': verified, 'wall_seconds': time.monotonic()-start, 'network_bytes': 0}
(out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
