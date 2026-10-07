"""Recover one verified BLTE object with at most two 24KiB archive range reads."""
import hashlib
import json
from pathlib import Path
import urllib.request
import urllib.error

from src.learning.casc_asset import verify_record

root = Path('logs/roadmap/old-casc-probe')
out = root / 'asset-archive-range-01'
out.mkdir(exist_ok=False)
index = Path('logs/roadmap/runtime-4.9.3/SC2Data/indices/8cae1b7aac0ede723affeeccc63689e9.index')
data = index.read_bytes()
key = '31271d461c33eda86a4723e3cbdd8038'
content_key = '1566ae22ab93ec0f9e246c9efbc7fec4'
footer = data[-36:]
assert footer[16:24] == bytes([1, 0, 0, 4, 4, 4, 16, 8])
assert hashlib.md5(footer[16:28] + bytes(8)).digest()[:8] == footer[28:]
offset = data.find(bytes.fromhex(key))
assert offset >= 0 and data.find(bytes.fromhex(key), offset + 1) == -1
assert (offset % 4096) % 24 == 0 and offset % 4096 + 24 <= 4096
size = int.from_bytes(data[offset + 16:offset + 20], 'big')
start = int.from_bytes(data[offset + 20:offset + 24], 'big')
assert size == 24624 and start == 17619227
end = start + size - 1
archive = index.stem
receipt = {'status': 'planned', 'encoded_key': key, 'content_key': content_key,
           'index_path': str(index), 'index_sha256': hashlib.sha256(data).hexdigest(),
           'footer_hash_verified': True, 'archive': archive, 'range': [start, end],
           'max_reserved_bytes': 2 * size, 'reserved_bytes': 0, 'network_bytes': 0,
           'attempts': [], 'installed': False,
           'scope': 'CDN BLTE/header/chunk/content verification; physical30byte local record header is synthetic and not archive evidence. No original game files or large ZIP prefix downloads.'}
def save():
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
save()
for host in ('us.cdn.blizzard.com', 'blzddist1-a.akamaihd.net'):
    url = f'https://{host}/tpr/sc2/data/{archive[:2]}/{archive[2:4]}/{archive}'
    receipt['reserved_bytes'] += size
    assert receipt['reserved_bytes'] <= receipt['max_reserved_bytes']
    attempt = {'url': url, 'reserved_bytes': size, 'status': 'reserved'}
    receipt['attempts'].append(attempt)
    save()
    try:
        request = urllib.request.Request(url, headers={'Range': f'bytes={start}-{end}', 'Accept-Encoding': 'identity'})
        with urllib.request.urlopen(request, timeout=30) as response:
            content_range = response.headers.get('Content-Range', '')
            assert response.status == 206 and content_range.startswith(f'bytes {start}-{end}/'), (response.status, content_range)
            assert int(content_range.split('/')[-1]) > end
            assert int(response.headers.get('Content-Length', size)) == size
            blte = response.read(size)
            receipt['network_bytes'] += len(blte)
            assert len(blte) == size
        # Existing decoder verifies BLTE header MD5, each chunk and full CKey.
        # This wrapper is solely an adapter, not a claimed physical CASC record.
        wrapped = bytes.fromhex(key)[::-1] + bytes(14) + blte
        decoded = verify_record(wrapped, key, content_key, 264581)
        (out / 'asset.blte').write_bytes(blte)
        (out / 'asset.decoded').write_bytes(decoded)
        attempt['status'] = 'verified'
        receipt.update(status='asset_integrity_verified_not_installed', blte_bytes=len(blte), decoded_bytes=len(decoded), blte_sha256=hashlib.sha256(blte).hexdigest(), decoded_sha256=hashlib.sha256(decoded).hexdigest())
        save()
        break
    except Exception as error:
        if isinstance(error, urllib.error.HTTPError):
            error.close()
        attempt.update(status='failed', error_type=type(error).__name__, error=str(error))
        save()
else:
    receipt['status'] = 'unavailable'
    save()
print(json.dumps(receipt, indent=2))
