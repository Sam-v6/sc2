"""Fixed bounded 4.9.3 encoding/root location probe; never launches SC2."""
import functools
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import zipfile
import zlib

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parents[2]))
from src.learning.zip_member import read_range, member_archive

URL = 'https://blzdistsc2-a.akamaihd.net/Linux/SC2.4.9.3.zip'
EKEY = '6a86cafee4bf07124a004b29d635717b'
CKEY = '8cdac468c0fc2fdf09812a057d805929'
ROOT = 'c305368c63621480462f8f516fb64374'
receipt = {'url': URL, 'prefix_budget': 48*1024**2, 'metadata_budget': 1024**2,
           'requests': [], 'format_source': 'https://github.com/ladislav-zezula/CascLib/blob/master/src/CascStructs.h'}

def fetch(start, length, category):
    used = sum(r['bytes'] for r in receipt['requests'] if r['category'] == category)
    assert used + length <= receipt[category + '_budget']
    path = BASE / f'range-{start}-{length}.bin'
    data = path.read_bytes() if path.exists() else read_range(URL, start, length)
    if not path.exists():
        path.write_bytes(data)
    assert len(data) == length
    receipt['requests'].append({'start': start, 'bytes': length, 'category': category,
        'sha256': hashlib.sha256(data).hexdigest()})
    (BASE/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return data

def main():
    decrypt = zipfile._ZipDecrypter(b'iagreetotheeula')
    inflate = zlib.decompressobj(-15)
    required = 113493 + 41725815
    out = bytearray()
    count = 0
    while len(out) < required:
        data = decrypt(fetch(246300585+count, 4*1024**2, 'prefix'))
        if count == 0:
            data = data[12:]
        out.extend(inflate.decompress(data, required-len(out)))
        count += 4*1024**2
        print('prefix', count, 'decoded', len(out), flush=True)
    record = bytes(out[113493:required])
    blte = record[30:]
    assert len(blte) == 41725785 and blte[:4] == b'BLTE'
    header_size = int.from_bytes(blte[4:8], 'big')
    assert hashlib.md5(blte[:header_size]).hexdigest() == EKEY
    assert blte[8] == 15
    chunks = int.from_bytes(blte[9:12], 'big')
    assert header_size == 12+24*chunks
    pos = header_size
    decoded = bytearray()
    for i in range(chunks):
        compressed, raw = struct.unpack_from('>II', blte, 12+24*i)
        checksum = blte[20+24*i:36+24*i]
        chunk = blte[pos:pos+compressed]
        assert len(chunk) == compressed and hashlib.md5(chunk).digest() == checksum
        assert chunk[:1] in (b'N', b'Z')
        payload = chunk[1:] if chunk[:1] == b'N' else zlib.decompress(chunk[1:])
        assert len(payload) == raw
        decoded.extend(payload)
        pos += compressed
    assert pos == len(blte) and len(decoded) == 41870246
    assert hashlib.md5(decoded).hexdigest() == CKEY
    (BASE/'encoding.blte').write_bytes(blte)
    (BASE/'encoding.decoded').write_bytes(decoded)
    receipt['encoding'] = {'ekey': EKEY, 'ckey': CKEY, 'chunks_verified': chunks,
        'encoded_size':len(blte), 'decoded_size':len(decoded), 'whole_zip_crc_verified':False,
        'sha256':hashlib.sha256(decoded).hexdigest()}
    assert decoded[:5] == b'EN\x01\x10\x10'
    page_size = int.from_bytes(decoded[5:7], 'big')*1024
    pages = int.from_bytes(decoded[9:13], 'big')
    table = 22+int.from_bytes(decoded[18:22], 'big')
    page_start = table+32*pages
    found = []
    for i in range(pages):
        page = decoded[page_start+i*page_size:page_start+(i+1)*page_size]
        assert hashlib.md5(page).digest() == decoded[table+32*i+16:table+32*i+32]
        assert page[6:22] == decoded[table+32*i:table+32*i+16]
        p = 0
        while p < len(page):
            n = int.from_bytes(page[p:p+2], 'little')
            if not n:
                break
            assert p+22+16*n <= len(page)
            if page[p+6:p+22].hex() == ROOT:
                found.append({'size':int.from_bytes(page[p+2:p+6],'big'),
                    'ekeys':[page[p+22+j*16:p+38+j*16].hex() for j in range(n)]})
            p += 22+16*n
    assert len(found) == 1
    receipt['root'] = found[0]
    receipt['root']['ckey'] = ROOT
    receipt['ckey_pages_verified'] = pages
    directory = fetch(3620389065,102054,'metadata')
    entries = []
    p = 0
    while p < len(directory):
        v = struct.unpack_from('<4s6H3L5H2L',directory,p)
        assert v[0] == b'PK\x01\x02'
        n,e,c = v[10:13]
        name = directory[p+46:p+46+n].decode()
        entries.append((name,v))
        p += 46+n+e+c
    locations = []
    for key in found[0]['ekeys']:
        short = bytes.fromhex(key)[:9]
        h = functools.reduce(int.__xor__,short)
        bucket = (h^(h>>4))&15
        matches = [(n,v) for n,v in entries if f'/SC2Data/data/{bucket:02x}' in n and n.endswith('.idx')]
        for name,v in matches:
            local = fetch(v[-1],30+len(name.encode())+v[8],'metadata')
            with zipfile.ZipFile(io.BytesIO(member_archive(local,name))) as archive:
                idx = archive.read(name,pwd=b'iagreetotheeula')
            assert zlib.crc32(idx) == v[7]
            assert idx[12:16] == bytes([4,5,9,30])
            i = idx.find(short)
            if i < 0:
                continue
            assert idx.find(short,i+1) == -1
            packed = int.from_bytes(idx[i+9:i+14],'big')
            number,offset = packed>>30,packed&((1<<30)-1)
            size = int.from_bytes(idx[i+14:i+18],'little')
            archive_name, av = next((n,w) for n,w in entries if n.endswith(f'/data.{number:03x}'))
            locations.append({'ekey':key,'index':name,'index_crc32':v[7],
                'archive':archive_name,'offset':offset,'record_size':size,
                'required_uncompressed_prefix':offset+size,'zip_method':av[4],
                'zip_compressed_size':av[8],'zip_raw_size':av[9],'zip_local_offset':av[-1]})
    assert locations
    receipt['root_locations'] = locations
    receipt['source_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    receipt['status'] = 'integrity_verified_root_located_no_runtime_claim'
    (BASE/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2),flush=True)

if __name__ == '__main__':
    main()
