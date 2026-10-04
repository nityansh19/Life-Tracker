from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.services.database import Database
from app.services.settings_service import SettingsService


class CloudSnapshotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(data_dir=Path(self.temp.name))
        self.db.initialize()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_snapshot_round_trip_preserves_tracker_data(self) -> None:
        with self.db.connection() as connection:
            connection.execute("UPDATE users SET name = 'Cloud Tester'")
            connection.execute(
                "UPDATE habits SET name = 'Cloud Habit' WHERE id = (SELECT MIN(id) FROM habits)"
            )
        snapshot = self.db.export_state()

        self.db.reset_user_state()
        self.db.import_state(snapshot)

        with self.db.connection() as connection:
            user = connection.execute("SELECT name FROM users ORDER BY id LIMIT 1").fetchone()
            habit = connection.execute("SELECT name FROM habits ORDER BY id LIMIT 1").fetchone()
        self.assertEqual(user["name"], "Cloud Tester")
        self.assertEqual(habit["name"], "Cloud Habit")

    def test_cloud_owner_is_device_local_only(self) -> None:
        SettingsService(self.db).set("cloud_owner_id", "user-a")
        snapshot = self.db.export_state()
        settings = {row["key"]: row["value"] for row in snapshot["settings"]}
        self.assertNotIn("cloud_owner_id", settings)

    def test_new_account_reset_returns_to_onboarding(self) -> None:
        SettingsService(self.db).set("onboarding_complete", True)
        self.db.reset_user_state()
        self.assertFalse(SettingsService(self.db).get_bool("onboarding_complete"))
        self.assertEqual(len(self.db.export_state()["habits"]), 8)


if __name__ == "__main__":
    unittest.main()
