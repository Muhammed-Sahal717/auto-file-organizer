import tempfile
import unittest
from pathlib import Path

from mover import move_file, resolve_duplicate_path


class MoverTests(unittest.TestCase):
    def test_move_file_creates_category_folder(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            src = root / "sample.pdf"
            src.write_text("demo", encoding="utf-8")

            destination = move_file(src, root, "PDFs")

            self.assertEqual(destination, root / "PDFs" / "sample.pdf")
            self.assertTrue(destination.exists())
            self.assertFalse(src.exists())

    def test_move_file_renames_duplicates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            destination_dir = root / "Images"
            destination_dir.mkdir()
            (destination_dir / "photo.jpg").write_text("existing", encoding="utf-8")

            src = root / "photo.jpg"
            src.write_text("new", encoding="utf-8")

            destination = move_file(src, root, "Images")

            self.assertEqual(destination.name, "photo(1).jpg")
            self.assertTrue(destination.exists())

    def test_dry_run_does_not_move_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            src = root / "notes.txt"
            src.write_text("demo", encoding="utf-8")

            destination = move_file(src, root, "Documents", dry_run=True)

            self.assertEqual(destination, root / "Documents" / "notes.txt")
            self.assertTrue(src.exists())
            self.assertFalse((root / "Documents").exists())

    def test_resolve_duplicate_path_keeps_original_when_available(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            candidate = Path(temp_dir) / "file.txt"
            self.assertEqual(resolve_duplicate_path(candidate), candidate)


if __name__ == "__main__":
    unittest.main()
