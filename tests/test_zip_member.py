import io
import unittest
import zipfile

try:
    from src.learning.zip_member import member_archive, validate_range
except ImportError:
    member_archive = validate_range = None


class ZipMemberTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(member_archive, "Bounded archive extraction is missing")

    def test_partial_archive_preserves_payload_and_crc(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("Versions/Base75025/SC2_x64", b"engine fixture bytes")
        archive = zipfile.ZipFile(io.BytesIO(stream.getvalue()))
        info = archive.infolist()[0]
        local = stream.getvalue()[: archive.start_dir]
        rebuilt = member_archive(local, info.filename)
        with zipfile.ZipFile(io.BytesIO(rebuilt)) as archive:
            self.assertEqual(archive.read(info.filename), b"engine fixture bytes")
        with self.assertRaises(ValueError):
            member_archive(local, "different/member")

    def test_range_validation_rejects_full_archive_or_wrong_cached_range(self):
        validate_range(206, "bytes 10-19/100", 10, 19)
        with self.assertRaises(ValueError):
            validate_range(200, None, 10, 19)
        with self.assertRaises(ValueError):
            validate_range(206, "bytes 0-9/100", 10, 19)
