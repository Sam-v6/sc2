"""Recover the traced asset. Offline by default; --download needs human approval."""
import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parents[2]))
from src.learning.casc_asset import extract_record, verify_record, MAX_PREFIX_BYTES
from src.learning.zip_member import validate_range


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--download', action='store_true')
    args = parser.parse_args()
    plan_path = BASE / 'required-assetsproduct-download-plan-01.json'
    plan = json.loads(plan_path.read_text())
    budget = plan['proposed_maximum_download_bytes']
    if not 12 <= budget <= MAX_PREFIX_BYTES:
        raise ValueError('Plan exceeds the 250 MiB input cap')
    args.output.mkdir(parents=True, exist_ok=False)
    receipt = {'status':'started', 'plan_sha256':hashlib.sha256(plan_path.read_bytes()).hexdigest(),
               'download_enabled':args.download, 'network_bytes':0, 'ranges':[],
               'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'decoder_sha256':hashlib.sha256((BASE.parents[2]/'src/learning/casc_asset.py').read_bytes()).hexdigest()}
    cache = BASE / 'assetsproduct-prefix-ranges'
    ledger_path = cache / 'download-budget.json'
    def save():
        (args.output/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    def read(offset, length):
        start = plan['encrypted_stream_start'] + offset
        path = cache / f'range-{start}-{length}.bin'
        cached = path.exists()
        if cached:
            data = path.read_bytes()
        else:
            if not args.download:
                raise FileNotFoundError('Required range is not cached; download authorization is still required')
            # Reserve before opening HTTP, including failed/interrupted attempts.
            cache.mkdir(exist_ok=True)
            with (cache/'budget.lock').open('a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {'plan_sha256':receipt['plan_sha256'], 'reserved_bytes':0, 'ranges':[]}
                if ledger['plan_sha256'] != receipt['plan_sha256']:
                    raise ValueError('Download ledger belongs to a different plan')
                receipt['reserved_network_bytes_cumulative'] = ledger['reserved_bytes']
                if ledger['reserved_bytes'] + length > budget:
                    raise ValueError('Cumulative download authorization exhausted')
                ledger['reserved_bytes'] += length
                ledger['ranges'].append({'start':start, 'bytes':length, 'attempt':str(args.output.resolve())})
                temporary = ledger_path.with_suffix('.tmp')
                temporary.write_text(json.dumps(ledger, indent=2)+'\n')
                temporary.replace(ledger_path)
                receipt['reserved_network_bytes_cumulative'] = ledger['reserved_bytes']
                save()
            # Exact bounded body read; reject full-file responses before reading.
            request = urllib.request.Request(plan['source'], headers={'Range':f'bytes={start}-{start+length-1}', 'Accept-Encoding':'identity'})
            with urllib.request.urlopen(request, timeout=30) as response:
                validate_range(response.status, response.headers.get('Content-Range'), start, start+length-1)
                data = response.read(length)
            receipt['network_bytes'] += len(data)
            if len(data) != length:
                raise ValueError('Incomplete bounded archive response')
            cache.mkdir(exist_ok=True)
            path.write_bytes(data)
        if len(data) != length:
            raise ValueError('Cached range has the wrong length')
        receipt['ranges'].append({'start':start, 'bytes':length, 'cached':cached, 'sha256':hashlib.sha256(data).hexdigest()})
        save()
        print(json.dumps({'input_bytes':offset+length, 'network_bytes':receipt['network_bytes']}), flush=True)
        return data
    try:
        record = extract_record(read, plan['record_offset'], plan['record_bytes'], budget)
        decoded = verify_record(record, plan['encoded_key'], plan['native_content_key'], 264581)
        (args.output/'asset.record').write_bytes(record)
        (args.output/'asset.decoded').write_bytes(decoded)
        receipt.update(status='asset_integrity_verified_not_installed', record_sha256=hashlib.sha256(record).hexdigest(), decoded_sha256=hashlib.sha256(decoded).hexdigest(), record_bytes=len(record), decoded_bytes=len(decoded), whole_zip_crc_verified=False)
    except BaseException as error:
        receipt.update(status='failed', error_type=type(error).__name__, error=str(error))
        save()
        raise
    save()
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
