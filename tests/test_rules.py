import unittest

from rules import RuleEngine


class RuleEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = RuleEngine(
            rules={
                "Images": [".jpg", ".png"],
                "PDFs": [".pdf"],
            },
            default_category="Others",
            ignored_extensions=[".tmp", ".crdownload"],
        )

    def test_known_extension_matches_category(self):
        self.assertEqual(self.engine.category_for("photo.JPG"), "Images")
        self.assertEqual(self.engine.category_for("report.pdf"), "PDFs")

    def test_unknown_extension_falls_back_to_default(self):
        self.assertEqual(self.engine.category_for("archive.xyz"), "Others")

    def test_temp_extensions_are_ignored(self):
        self.assertTrue(self.engine.should_ignore("download.crdownload"))
        self.assertTrue(self.engine.should_ignore("scratch.tmp"))
        self.assertFalse(self.engine.should_ignore("photo.png"))


if __name__ == "__main__":
    unittest.main()
