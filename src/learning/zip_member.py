"""Read a bounded, named member from a range-capable ZIP without bulk download."""

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import urllib.request
import zipfile


def validate_range(status, content_range, start, end):
    match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", content_range or "")
    if (
        status != 206
        or not match
        or tuple(map(int, match.groups()[:2])) != (start, end)
    ):
        raise ValueError("Server did not honor the exact bounded byte range")


def read_range(url, start, length):
    end = start + length - 1
    request = urllib.request.Request(
        url, headers={"Range": f"bytes={start}-{end}", "Accept-Encoding": "identity"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        validate_range(
            response.status, response.headers.get("Content-Range"), start, end
        )
        data = response.read(length + 1)
    if len(data) != length:
        raise ValueError("Range response has the wrong byte count")
    return data


def member_archive(local, member):
    fields = struct.unpack("<4s5H3I2H", local[:30])
    (
        signature,
        version,
        flags,
        method,
        time,
        date,
        crc,
        compressed,
        raw,
        name_len,
        extra_len,
    ) = fields
    name = local[30 : 30 + name_len]
    if signature != b"PK\x03\x04" or name.decode("utf-8") != member or flags & 8:
        raise ValueError(
            "ZIP local header does not describe the expected complete member"
        )
    if len(local) != 30 + name_len + extra_len + compressed:
        raise ValueError("ZIP member is incomplete")
    central = (
        struct.pack(
            "<4s6H3I5H2I",
            b"PK\x01\x02",
            version,
            version,
            flags,
            method,
            time,
            date,
            crc,
            compressed,
            raw,
            name_len,
            0,
            0,
            0,
            0,
            0,
            0,
        )
        + name
    )
    end = struct.pack(
        "<4s4H2IH", b"PK\x05\x06", 0, 0, 1, 1, len(central), len(local), 0
    )
    return local + central + end


def fetch_member(url, offset, member, output, max_bytes, crc=None):
    if output.exists():
        raise FileExistsError(output)
    header = read_range(url, offset, 30)
    fields = struct.unpack("<4s5H3I2H", header)
    compressed, raw, name_len, extra_len = fields[7:11]
    if compressed > max_bytes or raw > 4 * max_bytes or name_len + extra_len > 4096:
        raise ValueError("ZIP member exceeds the declared download/extraction budget")
    if crc is not None and fields[6] != crc:
        raise ValueError(
            "ZIP header CRC differs from the independently inspected directory"
        )
    rest = read_range(url, offset + 30, name_len + extra_len + compressed)
    archive_bytes = member_archive(header + rest, member)
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        payload = archive.read(member, pwd=b"iagreetotheeula")
    if len(payload) != raw:
        raise ValueError("Extracted size mismatch")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write(payload)
    receipt = {
        "source": url,
        "member": member,
        "local_header_offset": offset,
        "download_bytes": len(header) + len(rest),
        "bytes": len(payload),
        "crc32": fields[6],
        "sha256": hashlib.sha256(payload).hexdigest(),
    }
    output.with_suffix(output.suffix + ".source.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--offset", type=int, required=True)
    parser.add_argument("--member", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-bytes", type=int, required=True)
    parser.add_argument("--crc", type=lambda x: int(x, 0))
    args = parser.parse_args()
    if args.offset < 0 or args.max_bytes < 1:
        parser.error("Offset and budget must be nonnegative/positive")
    print(
        json.dumps(
            fetch_member(
                args.url,
                args.offset,
                args.member,
                args.output,
                args.max_bytes,
                args.crc,
            )
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
