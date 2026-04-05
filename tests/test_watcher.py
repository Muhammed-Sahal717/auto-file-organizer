import tempfile
import unittest
from pathlib import Path
from unittest import mock

from rules import RuleEngine
from watcher import OrganizerEventHandler, organize_existing_files


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


class WatcherEventTests(unittest.TestCase):
    def setUp(self):
        self.engine = RuleEngine(
            rules={
                "Images": [".jpg", ".png"],
                "PDFs": [".pdf"],
            },
            default_category="Others",
            ignored_extensions=[".tmp", ".crdownload"],
        )

    def test_moved_file_into_top_level_is_organized(self):
        handler = OrganizerEventHandler(
            watch_path="/tmp/watch-root",
            rule_engine=self.engine,
            stability_checks=0,
            stability_delay=0,
        )
        event = mock.Mock(
            is_directory=False,
            src_path="/tmp/watch-root/file.crdownload",
            dest_path="/tmp/watch-root/photo.jpg",
        )

        with mock.patch("watcher.organize_file") as organize_file_mock:
            handler.handle_moved(event)

        organize_file_mock.assert_called_once()
        self.assertEqual(
            organize_file_mock.call_args.kwargs["src_path"],
            Path("/tmp/watch-root/photo.jpg"),
        )

    def test_moved_file_into_subfolder_is_ignored(self):
        handler = OrganizerEventHandler(
            watch_path="/tmp/watch-root",
            rule_engine=self.engine,
            stability_checks=0,
            stability_delay=0,
        )
        event = mock.Mock(
            is_directory=False,
            src_path="/tmp/watch-root/photo.jpg",
            dest_path="/tmp/watch-root/Images/photo.jpg",
        )

        with mock.patch("watcher.organize_file") as organize_file_mock:
            handler.handle_moved(event)

        organize_file_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
