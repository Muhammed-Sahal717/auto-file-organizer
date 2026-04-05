import os
import tempfile
import unittest
from pathlib import Path

from utils import (
    get_running_pid,
    process_is_running,
    read_pid_file,
    remove_pid_file,
    write_pid_file,
)


class PidUtilsTests(unittest.TestCase):
    def test_write_and_read_pid_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pid_path = Path(temp_dir) / "organizer.pid"

            write_pid_file(12345, pid_path)

            self.assertEqual(read_pid_file(pid_path), 12345)

    def test_remove_pid_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pid_path = Path(temp_dir) / "organizer.pid"
            write_pid_file(12345, pid_path)

            remove_pid_file(pid_path)

            self.assertFalse(pid_path.exists())

    def test_process_is_running_detects_current_process(self):
        self.assertTrue(process_is_running(os.getpid()))

    def test_get_running_pid_cleans_stale_pid_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pid_path = Path(temp_dir) / "organizer.pid"
            write_pid_file(999999, pid_path)

            self.assertIsNone(get_running_pid(pid_path))
            self.assertFalse(pid_path.exists())


if __name__ == "__main__":
    unittest.main()
