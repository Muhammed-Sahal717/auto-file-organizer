import tempfile
import unittest
from pathlib import Path

from rules import RuleEngine
from watcher import organize_existing_files


class ExistingFileScanTests(unittest.TestCase):
    def setUp(self):
        self.engine = RuleEngine(
            rules={
                "Images": [".jpg", ".png"],
                "PDFs": [".pdf"],
            },
            default_category="Others",
            ignored_extensions=[".tmp", ".crdownload"],
        )

    def test_existing_files_are_organized_from_top_level_only(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "photo.jpg").write_text("image", encoding="utf-8")
            (root / "report.pdf").write_text("pdf", encoding="utf-8")
            (root / "ignore.tmp").write_text("temp", encoding="utf-8")

            images_dir = root / "Images"
            images_dir.mkdir()
            (images_dir / "already.jpg").write_text("keep", encoding="utf-8")

            nested_dir = root / "nested"
            nested_dir.mkdir()
            (nested_dir / "inside.png").write_text("nested", encoding="utf-8")

            organized_count = organize_existing_files(
                watch_path=root,
                rule_engine=self.engine,
                stability_checks=0,
                stability_delay=0,
            )

            self.assertEqual(organized_count, 2)
            self.assertTrue((root / "Images" / "photo.jpg").exists())
            self.assertTrue((root / "PDFs" / "report.pdf").exists())
            self.assertTrue((root / "Images" / "already.jpg").exists())
            self.assertTrue((root / "nested" / "inside.png").exists())
            self.assertTrue((root / "ignore.tmp").exists())

    def test_existing_file_scan_supports_dry_run(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "notes.pdf").write_text("pdf", encoding="utf-8")

            organized_count = organize_existing_files(
                watch_path=root,
                rule_engine=self.engine,
                dry_run=True,
                stability_checks=0,
                stability_delay=0,
            )

            self.assertEqual(organized_count, 1)
            self.assertTrue((root / "notes.pdf").exists())
            self.assertFalse((root / "PDFs").exists())


if __name__ == "__main__":
    unittest.main()
