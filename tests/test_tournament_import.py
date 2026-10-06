import tempfile
from pathlib import Path
import unittest

from src.learning.tournament_import import check_bindings, digest


class TournamentImportTests(unittest.TestCase):
    def test_changed_source_binding_cannot_enter_import(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source.bin"
            source.write_bytes(b"original")
            receipt = dict(bindings={str(source): digest(source)})
            check_bindings(receipt)
            source.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "Changed source binding"):
                check_bindings(receipt)
