import sys
import unittest
from unittest import mock

from autostart import (
    build_linux_service_content,
    build_mac_plist_content,
    build_runtime_command,
    build_windows_task_command,
    linux_service_enablement_status,
    linux_service_is_active,
)


class AutostartTests(unittest.TestCase):
    def test_build_runtime_command_for_source_checkout(self):
        command = build_runtime_command("~/Downloads", config_path="config.json", dry_run=True)

        self.assertEqual(command[0], sys.executable)
        self.assertTrue(command[1].endswith("organizer.py"))
        self.assertIn("--run-service", command)
        self.assertIn("--dry-run", command)
        self.assertIn("--config", command)

    def test_build_runtime_command_for_frozen_binary(self):
        with mock.patch.object(sys, "frozen", True, create=True):
            with mock.patch.object(sys, "executable", "/tmp/dist/organizer"):
                command = build_runtime_command("~/Downloads")

        self.assertEqual(command[0], "/tmp/dist/organizer")
        self.assertNotIn("organizer.py", command)
        self.assertIn("--run-service", command)

    def test_linux_service_content_contains_execstart(self):
        content = build_linux_service_content(["/usr/bin/python3", "/app/organizer.py"])

        self.assertIn("ExecStart=/usr/bin/python3 /app/organizer.py", content)
        self.assertIn("Restart=always", content)

    def test_mac_plist_contains_program_arguments(self):
        content = build_mac_plist_content(["/usr/bin/python3", "/app/organizer.py"])

        self.assertIn("<string>/usr/bin/python3</string>", content)
        self.assertIn("<string>/app/organizer.py</string>", content)
        self.assertIn("<key>RunAtLoad</key>", content)

    def test_windows_task_command_preserves_arguments(self):
        command = build_windows_task_command(
            ["C:\\Program Files\\Organizer\\organizer.exe", "--run-service"]
        )

        self.assertIn("organizer.exe", command)
        self.assertIn("--run-service", command)

    def test_linux_service_is_active_reads_systemctl_output(self):
        completed = mock.Mock(stdout="active\n", returncode=0)

        with mock.patch("autostart.sys.platform", "linux"):
            with mock.patch("autostart.linux_service_path", return_value=mock.Mock(exists=lambda: True)):
                with mock.patch("autostart._run_linux_systemctl", return_value=completed):
                    self.assertTrue(linux_service_is_active())

    def test_linux_service_enablement_status_reads_systemctl_output(self):
        completed = mock.Mock(stdout="enabled\n", stderr="", returncode=0)

        with mock.patch("autostart.sys.platform", "linux"):
            with mock.patch("autostart.linux_service_path", return_value=mock.Mock(exists=lambda: True)):
                with mock.patch("autostart._run_linux_systemctl", return_value=completed):
                    self.assertEqual(linux_service_enablement_status(), "enabled")


if __name__ == "__main__":
    unittest.main()
