"""Recover and verify one CASC record from a bounded encrypted ZIP prefix."""

import hashlib
import struct
import zipfile
import zlib


MAX_PREFIX_BYTES = 250 * 1024**2
DECODE_CHUNK_BYTES = 1024**2


def extract_record(read, offset, size, budget, chunk_bytes=4 * 1024**2):
    """Read relative stream ranges; retain only the requested decoded record.

    The caller supplies cached or authorized range reads. This does not verify
    the entire ZIP member's CRC or install anything into a game directory.
    """
    if (
        offset < 0
        or not 0 < size <= MAX_PREFIX_BYTES
        or not 12 <= budget <= MAX_PREFIX_BYTES
    ):
        raise ValueError("Invalid record range or prefix byte budget")
    if chunk_bytes < 13:
        raise ValueError("First chunk must include the ZIP encryption header")
    decrypt = zipfile._ZipDecrypter(b"iagreetotheeula")
    inflate = zlib.decompressobj(-15)
    consumed = position = 0
    result = bytearray()
    end = offset + size
    while position < end:
        length = min(chunk_bytes, budget - consumed)
        if not length:
            raise ValueError("Prefix byte budget exhausted before requested record")
        data = read(consumed, length)
        if len(data) != length:
            raise ValueError("Incomplete prefix range")
        plaintext = decrypt(data)
        if not consumed:
            plaintext = plaintext[12:]
        consumed += length
        while position < end:
            limit = min(DECODE_CHUNK_BYTES, end - position)
            decoded = inflate.decompress(plaintext, limit)
            overlap = max(offset - position, 0)
            if overlap < len(decoded):
                result.extend(decoded[overlap:])
            position += len(decoded)
            plaintext = inflate.unconsumed_tail
            if not plaintext and len(decoded) < limit:
                break
        if inflate.eof and position < end:
            raise ValueError("ZIP stream ended before requested record")
    if len(result) != size:
        raise ValueError("Decoded record has the wrong size")
    return bytes(result)


def verify_record(record, encoded_key, content_key, decoded_size):
    """Verify physical key, framed BLTE hashes and complete decoded content."""
    if not 0 < decoded_size <= MAX_PREFIX_BYTES or len(record) > MAX_PREFIX_BYTES:
        raise ValueError("CASC content exceeds the retained-output limit")
    if len(record) < 42 or record[:16][::-1].hex() != encoded_key:
        raise ValueError("CASC record key is incorrect")
    blte = record[30:]
    header_size = int.from_bytes(blte[4:8], "big")
    chunks = int.from_bytes(blte[9:12], "big")
    if (
        blte[:4] != b"BLTE"
        or blte[8] != 15
        or not chunks
        or header_size != 12 + 24 * chunks
        or header_size > len(blte)
        or hashlib.md5(blte[:header_size]).hexdigest() != encoded_key
    ):
        raise ValueError("Unsupported or corrupt BLTE header")
    position = header_size
    decoded = bytearray()
    for index in range(chunks):
        entry = 12 + 24 * index
        compressed, raw = struct.unpack_from(">II", blte, entry)
        chunk = blte[position : position + compressed]
        if (
            not compressed
            or len(chunk) != compressed
            or len(decoded) + raw > decoded_size
            or hashlib.md5(chunk).digest() != blte[entry + 8 : entry + 24]
        ):
            raise ValueError("Corrupt or oversized BLTE frame")
        if chunk[:1] == b"N":
            payload = chunk[1:]
        elif chunk[:1] == b"Z":
            inflater = zlib.decompressobj()
            payload = inflater.decompress(chunk[1:], raw + 1)
            if not inflater.eof or inflater.unused_data or inflater.unconsumed_tail:
                raise ValueError("Incomplete or oversized compressed BLTE frame")
        else:
            raise ValueError("Unsupported BLTE frame encoding")
        if len(payload) != raw:
            raise ValueError("BLTE decoded frame has the wrong size")
        decoded.extend(payload)
        position += compressed
    if (
        position != len(blte)
        or len(decoded) != decoded_size
        or hashlib.md5(decoded).hexdigest() != content_key
    ):
        raise ValueError("Decoded CASC content integrity failed")
    return bytes(decoded)
