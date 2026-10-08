import hashlib
import io
import json
from pathlib import Path
import struct
import urllib.request
import zipfile

root = Path(__file__).parent
url = 'https://blzdistsc2-a.akamaihd.net/Linux/SC2.4.10.zip'
size = 4115224017
budget = 512 * 1024
spent = 65536  # First bounded probe already downloaded one tail.
transfers = []
(root/'linux-archive-metadata-contract-01.json').write_text(json.dumps(dict(
    url=url, maximum_download_bytes=budget, scope='ZIP directory only; no executables or assets'),indent=2)+'\n')
def fetch(start, count):
    global spent
    assert spent + count <= budget
    req = urllib.request.Request(url, headers={'Range':f'bytes={start}-{start+count-1}', 'Accept-Encoding':'identity'})
    with urllib.request.urlopen(req, timeout=20) as response:
        assert response.status == 206
        assert response.headers.get('Content-Range') == f'bytes {start}-{start+count-1}/{size}'
        data = response.read(count+1)
        assert len(data) == count
    spent += count
    transfers.append(dict(start=start, count=count, sha256=hashlib.sha256(data).hexdigest()))
    return data
last = fetch(size-65536, 65536)
(root/'linux-archive-tail-01.bin').write_bytes(last)
pos = last.rfind(b'PK\x05\x06')
assert pos >= 0
end = bytearray(last[pos:])
_, disk, directory_disk, entries_here, entries, length, offset, comment = struct.unpack_from('<4s4H2IH', end)
assert disk == directory_disk == 0 and entries_here == entries and len(end) == 22 + comment
assert offset + length == size - len(end)
print(dict(directory_bytes=length,directory_entries=entries),flush=True)
if length + spent > budget:
    # Inspect only complete entries in the retained tail; do not claim that
    # this is the entire directory.
    central = last[:pos]
    first=central.find(b'PK\x01\x02')
    assert first>=0
    central=central[first:]
    end=bytearray(22)
    end[:4]=b'PK\x05\x06'
    cursor=count=0
    while cursor<len(central):
        assert central[cursor:cursor+4]==b'PK\x01\x02'
        a,b,c=struct.unpack_from('<HHH',central,cursor+28)
        cursor+=46+a+b+c;count+=1
    assert cursor==len(central)
    struct.pack_into('<HHII',end,8,count,count,len(central),0)
elif offset >= size-65536:
    central = last[offset-(size-65536):offset-(size-65536)+length]
else:
    central = fetch(offset, length)
struct.pack_into('<I', end, 16, 0)
with zipfile.ZipFile(io.BytesIO(central+end)) as archive:
    rows = [dict(name=i.filename,compressed_bytes=i.compress_size,bytes=i.file_size,
                 offset=i.header_offset,method=i.compress_type,flags=i.flag_bits)
            for i in archive.infolist() if '/Versions/' in i.filename]
(root/'linux-archive-directory-01.bin').write_bytes(central)
result=dict(url=url,total_archive_bytes=size,directory_entries=entries,
    downloaded_bytes=spent,transfers=transfers,versions=rows,
    full_directory_read=length+65536 <= budget,original_directory_bytes=length,
    base76052_present_in_read_entries=any('/Base76052/' in i['name'] for i in rows),
    executable_or_asset_download_bytes=0)
(root/'linux-archive-metadata-01.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
