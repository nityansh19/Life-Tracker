from __future__ import annotations

import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from app.services.analytics_service import AnalyticsService
from app.services.database import Database
from app.services.day_service import DayService
from app.services.habit_service import HabitService
from app.services.streak_service import StreakService


class ArcCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(data_dir=Path(self.temp.name))
        self.db.initialize()
        self.habits = HabitService(self.db)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_starter_habits_seed_once(self) -> None:
        self.assertEqual(len(self.habits.get_all_habits()), 8)
        self.db.initialize()
        self.assertEqual(len(self.habits.get_all_habits()), 8)

    def test_custom_weekday_schedule(self) -> None:
        habit_id = self.habits.create_habit(
            name="Monday review",
            category="Productivity",
            goal_type="boolean",
            goal_amount=1,
            unit="completion",
            required=False,
            schedule="mon",
        )
        monday = date.today() + timedelta(days=(7 - date.today().weekday()) % 7)
        if monday == date.today() and date.today().weekday() != 0:
            monday += timedelta(days=7)
        tuesday = monday + timedelta(days=1)
        monday_ids = {habit.id for habit in self.habits.get_habits(monday)}
        tuesday_ids = {habit.id for habit in self.habits.get_habits(tuesday)}
        self.assertIn(habit_id, monday_ids)
        self.assertNotIn(habit_id, tuesday_ids)

    def test_habit_xp_cannot_be_farmed(self) -> None:
        workout = next(h for h in self.habits.get_all_habits() if h.name == "Workout")
        self.habits.toggle_boolean(workout.id)
        self.habits.toggle_boolean(workout.id)
        self.habits.toggle_boolean(workout.id)
        with self.db.connection() as connection:
            events = connection.execute(
                "SELECT COUNT(*) FROM xp_events WHERE event_key = ?",
                (f"habit:{date.today().isoformat()}:{workout.id}",),
            ).fetchone()[0]
        self.assertEqual(events, 1)

    def test_perfect_day_awarded_once(self) -> None:
        today = date.today().isoformat()
        for habit in self.habits.get_habits(today):
            if not habit.required:
                continue
            if habit.goal_type == "boolean":
                self.habits.toggle_boolean(habit.id, today)
            else:
                self.habits.set_value(habit.id, habit.goal_amount, today)

        result = self.habits.evaluate_day(today)
        self.assertTrue(result["day_completed"])
        with self.db.connection() as connection:
            before = connection.execute("SELECT xp FROM users ORDER BY id LIMIT 1").fetchone()[0]
            event_count = connection.execute(
                "SELECT COUNT(*) FROM xp_events WHERE event_key = ?",
                (f"perfect_day:{today}",),
            ).fetchone()[0]
        self.assertEqual(event_count, 1)
        self.habits.evaluate_day(today)
        with self.db.connection() as connection:
            after = connection.execute("SELECT xp FROM users ORDER BY id LIMIT 1").fetchone()[0]
        self.assertEqual(before, after)

    def test_streak_is_derived_from_dates(self) -> None:
        yesterday = date.today() - timedelta(days=1)
        dates = [yesterday - timedelta(days=2), yesterday - timedelta(days=1), yesterday]
        with self.db.connection() as connection:
            for day in dates:
                connection.execute(
                    """
                    INSERT OR REPLACE INTO daily_completion(
                        date, completed, completion_percentage, scheduled_required,
                        completed_required, completed_at, updated_at
                    ) VALUES (?, 1, 100, 1, 1, ?, ?)
                    """,
                    (day.isoformat(), day.isoformat(), day.isoformat()),
                )
        streak = StreakService(self.db).snapshot()
        self.assertEqual(streak["current_streak"], 3)
        self.assertEqual(streak["longest_streak"], 3)

    def test_missed_days_are_backfilled(self) -> None:
        start = date.today() - timedelta(days=3)
        with self.db.connection() as connection:
            connection.execute(
                "UPDATE users SET journey_start_date = ?",
                (start.isoformat(),),
            )
        DayService(self.db).sync_history()
        with self.db.connection() as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM daily_completion WHERE date < ?",
                (date.today().isoformat(),),
            ).fetchone()[0]
        self.assertEqual(count, 3)

    def test_weekly_report_has_required_fields(self) -> None:
        report = AnalyticsService(self.db).weekly_report()
        for key in (
            "completion_percentage",
            "perfect_days",
            "workouts",
            "average_steps",
            "average_water_ml",
            "study_minutes",
            "message",
        ):
            self.assertIn(key, report)


if __name__ == "__main__":
    unittest.main()
