"""Read-only exact old-content lookup in the installed current encoding manifest."""
import hashlib
import json
from pathlib import Path

from src.learning.casc_asset import verify_record

installed = Path('/home/sam/repos/sc2-repos/game/SC2.4.10/StarCraftII')
out = Path('logs/roadmap/old-casc-probe/current-content-key-01')
out.mkdir(exist_ok=False)
config = installed / 'SC2Data/config/fe/31/fe312cd843e1f213344f61a396653957'
fields = {line.split(' = ')[0]: line.split(' = ')[1] for line in config.read_text().splitlines() if ' = ' in line}
ckey, ekey = fields['encoding'].split()
decoded_size, encoded_size = map(int, fields['encoding-size'].split())
index = {}
bindings = {str(config): hashlib.sha256(config.read_bytes()).hexdigest()}
for bucket in range(16):
    path = max((installed / 'SC2Data/data').glob(f'{bucket:02x}*.idx'))
    data = path.read_bytes()
    assert data[8:16] == bytes([7, 0, bucket, 0, 4, 5, 9, 30])
    length = int.from_bytes(data[32:36], 'little')
    assert length % 18 == 0 and 40 + length <= len(data)
    bindings[str(path)] = hashlib.sha256(data).hexdigest()
    for pos in range(40, 40 + length, 18):
        index[data[pos:pos+9]] = data[pos+9:pos+18]

def local_record(key):
    entry = index.get(bytes.fromhex(key)[:9])
    if entry is None:
        return None
    address = int.from_bytes(entry[:5], 'big')
    size = int.from_bytes(entry[5:], 'little')
    assert 0 < size <= 250 * 1024**2
    path = installed / f'SC2Data/data/data.{address >> 30:03x}'
    offset = address & ((1 << 30) - 1)
    assert offset + size <= path.stat().st_size
    with path.open('rb') as stream:
        stream.seek(offset)
        record = stream.read(size)
    assert len(record) == size and record[:16][::-1].hex() == key
    return record, {'path': str(path), 'offset': offset, 'bytes': size, 'record_sha256': hashlib.sha256(record).hexdigest()}

record, manifest_location = local_record(ekey)
assert len(record) in (encoded_size, encoded_size + 30)
encoding = verify_record(record, ekey, ckey, decoded_size)
assert encoding[:5] == b'EN\x01\x10\x10'
page_size = int.from_bytes(encoding[5:7], 'big') * 1024
pages = int.from_bytes(encoding[9:13], 'big')
table = 22 + int.from_bytes(encoding[18:22], 'big')
begin = table + 32 * pages
required = '1566ae22ab93ec0f9e246c9efbc7fec4'
matches = []
entries = 0
for page_index in range(pages):
    page = encoding[begin + page_index * page_size:begin + (page_index + 1) * page_size]
    assert len(page) == page_size
    assert hashlib.md5(page).digest() == encoding[table + 32 * page_index + 16:table + 32 * page_index + 32]
    pos = 0
    while pos < len(page):
        count = int.from_bytes(page[pos:pos+2], 'little')
        if not count:
            break
        assert pos + 22 + 16 * count <= len(page)
        entries += 1
        content = page[pos+6:pos+22].hex()
        if content == required:
            size = int.from_bytes(page[pos+2:pos+6], 'big')
            keys = [page[pos+22+16*j:pos+38+16*j].hex() for j in range(count)]
            matches.append({'content_key': content, 'decoded_bytes': size, 'encoded_keys': keys})
        pos += 22 + 16 * count
verified = []
for match in matches:
    assert match['decoded_bytes'] == 264581
    for key in match['encoded_keys']:
        found = local_record(key)
        if found:
            record, location = found
            decoded = verify_record(record, key, required, 264581)
            (out / f'{key}.record').write_bytes(record)
            (out / f'{key}.decoded').write_bytes(decoded)
            verified.append(dict(location, encoded_key=key, decoded_sha256=hashlib.sha256(decoded).hexdigest()))
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == digest for p,digest in bindings.items())
report = {'status': 'verified_exact_content_recovered' if verified else 'exact_content_unavailable_locally', 'scope': 'Exact old CKey lookup, not a substitute current AssetsProduct. Read-only original installation; no network or installation.', 'bindings': bindings, 'manifest': dict(manifest_location, content_key=ckey, encoded_key=ekey, decoded_bytes=decoded_size, decoded_sha256=hashlib.sha256(encoding).hexdigest(), pages_verified=pages, entries_scanned=entries), 'required_content_key': required, 'matches': matches, 'locally_verified_representations': verified, 'network_bytes': 0}
(out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
