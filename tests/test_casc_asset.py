import base64
import hashlib
import struct
import unittest
from unittest.mock import patch
import zlib

try:
    from src.learning.casc_asset import extract_record, verify_record
except ImportError:
    extract_record = verify_record = None


# Deflated and ZipCrypto-encrypted by the system zip utility, not this decoder.
STREAM = base64.b64decode(
    "vYwe7JfDwB1BrzKceKsPmANYzf1060IlG0Z3WT+6ckJ3aD0+0SubhEDoRfwfgy9YgfN8WdhfJUDJQtV581pUtY5vSEi6LjyD6gaL5gndaoLoFK8KCNE4HAV0Fd42iwdkVcpeXsPUPhBFpaR7BMP1maMQKX02OhJJWFt8D2e/9QsrFjhxx/GVayKDtdiD9Zqi28XeCLQz1dEKV7BDKtCBgZk5kFocInYYSudO0OPIbkp6DJL1a8so07RAlOe8m7m++InCKESBXOvNpoKsfipA77jClGwzn/LKwGfQ/uY+vx3ZA6cYqGgHGPAP/Y4a6zUlMw0HJuVY9rUTVMPKxs7U5I69taR3NuKLgTvlZWLomJpYSfIgy2FdzUGRPMN4PyWuE+rpQb/Qy97eUIo19prYmQxYsGxB2cDFQUkFVzsyHvcJ3y5pWfq2J/13vkBIhJ9cl0St6QPjqLkYdyXyhmuv845FKWl+HoKXDHFv2eVDT/bsvNnOSmt0JqtX62HT5OxgAXvQp4Gq1ndbfL4HB4ovFPq1B16lWxnLHcWk1Nl36yaEAtziT2dxHbb4ng=="
)


def record_fixture():
    payloads = [b"first decoded frame", b"second frame" * 100]
    chunks = [b"N" + payloads[0], b"Z" + zlib.compress(payloads[1])]
    header = b"BLTE" + struct.pack(">I", 60) + b"\x0f\x00\x00\x02"
    for chunk, payload in zip(chunks, payloads):
        header += struct.pack(">II", len(chunk), len(payload))
        header += hashlib.md5(chunk).digest()
    ekey = hashlib.md5(header).digest()
    record = ekey[::-1] + bytes(14) + header + b"".join(chunks)
    content = b"".join(payloads)
    return record, ekey.hex(), hashlib.md5(content).hexdigest(), content


class CascAssetTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            extract_record, "Bounded encrypted-prefix recovery missing"
        )

    def test_encrypted_prefix_recovers_record_across_chunk_boundaries(self):
        requests = []

        def read(start, length):
            requests.append((start, length))
            return STREAM[start : start + length]

        result = extract_record(read, 5120, 45, len(STREAM), chunk_bytes=31)
        self.assertEqual(result, b"verified-record" * 3)
        self.assertLess(sum(length for _, length in requests), len(STREAM))

    def test_budget_is_enforced_before_request_and_final_request_is_clipped(self):
        requests = []

        def read(start, length):
            requests.append((start, length))
            return STREAM[start : start + length]

        with self.assertRaises(ValueError):
            extract_record(read, 5120, 45, 100, chunk_bytes=31)
        self.assertEqual(sum(length for _, length in requests), 100)
        self.assertEqual(requests[-1], (93, 7))

    def test_short_read_cannot_be_used_as_complete_record(self):
        with self.assertRaises(ValueError):
            extract_record(lambda start, length: b"", 5120, 45, 100)

    def test_budget_over_250_mib_is_rejected_before_any_read(self):
        with self.assertRaises(ValueError):
            extract_record(None, 0, 1, 250 * 1024**2 + 1)

    def test_retained_record_over_250_mib_is_rejected_before_any_read(self):
        with self.assertRaises(ValueError):
            extract_record(None, 0, 250 * 1024**2 + 1, 100)

    def test_skipped_high_expansion_prefix_is_drained_in_bounded_chunks(self):
        compressor = zlib.compressobj(wbits=-15)
        data = bytes(12) + compressor.compress(bytes(2 * 1024**2) + b"end")
        data += compressor.flush()
        real = zlib.decompressobj(-15)
        decoded_lengths = []

        class TrackedInflater:
            def decompress(self, data, limit):
                result = real.decompress(data, limit)
                decoded_lengths.append(len(result))
                return result

            def __getattr__(self, name):
                return getattr(real, name)

        with (
            patch(
                "src.learning.casc_asset.zipfile._ZipDecrypter",
                return_value=lambda b: b,
            ),
            patch(
                "src.learning.casc_asset.zlib.decompressobj",
                return_value=TrackedInflater(),
            ),
        ):
            result = extract_record(
                lambda start, size: data[start : start + size],
                2 * 1024**2,
                3,
                len(data),
            )
        self.assertEqual(result, b"end")
        self.assertLessEqual(max(decoded_lengths), 1024**2)

    def test_decoded_frame_size_is_bounded_before_content_is_retained(self):
        chunk = b"Z" + zlib.compress(b"expanded" * 10000)
        header = b"BLTE" + struct.pack(">I", 36) + b"\x0f\x00\x00\x01"
        header += struct.pack(">II", len(chunk), 1) + hashlib.md5(chunk).digest()
        ekey = hashlib.md5(header).digest()
        record = ekey[::-1] + bytes(14) + header + chunk
        with self.assertRaises(ValueError):
            verify_record(record, ekey.hex(), "00" * 16, 1)

    def test_framed_content_requires_encoded_and_decoded_integrity(self):
        record, ekey, ckey, content = record_fixture()
        self.assertEqual(verify_record(record, ekey, ckey, len(content)), content)
        damaged = bytearray(record)
        damaged[-1] ^= 1
        with self.assertRaises(ValueError):
            verify_record(damaged, ekey, ckey, len(content))
        with self.assertRaises(ValueError):
            verify_record(record, "00" * 16, ckey, len(content))
        with self.assertRaises(ValueError):
            verify_record(record, ekey, "00" * 16, len(content))
        with self.assertRaises(ValueError):
            verify_record(record, ekey, ckey, len(content) - 1)


if __name__ == "__main__":
    unittest.main()
