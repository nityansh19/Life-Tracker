from __future__ import annotations

from datetime import datetime

from app.models.habit import Habit
from app.services.database import Database
from app.services.streak_service import StreakService
from app.utils.dates import today_iso


class HabitService:
    def __init__(self, database: Database) -> None:
        self.database = database
        self.streaks = StreakService(database)

    def get_habits(self) -> list[Habit]:
        with self.database.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM habits WHERE active = 1 ORDER BY required DESC, id ASC"
            ).fetchall()
        return [Habit.from_row(row) for row in rows]

    def get_progress_map(self, day: str | None = None) -> dict[int, dict[str, float | bool]]:
        day = day or today_iso()
        with self.database.connection() as connection:
            rows = connection.execute(
                "SELECT habit_id, value, completed FROM daily_habit_progress WHERE date = ?",
                (day,),
            ).fetchall()
        return {
            row["habit_id"]: {"value": float(row["value"]), "completed": bool(row["completed"])}
            for row in rows
        }

    def toggle_boolean(self, habit_id: int) -> None:
        day = today_iso()
        progress = self.get_progress_map(day).get(habit_id, {"completed": False})
        new_value = 0 if progress["completed"] else 1
        self._write_progress(habit_id, day, new_value)
        self.evaluate_day(day)

    def increment(self, habit_id: int, amount: float) -> None:
        day = today_iso()
        progress = self.get_progress_map(day).get(habit_id, {"value": 0.0})
        new_value = max(0, float(progress["value"]) + amount)
        self._write_progress(habit_id, day, new_value)
        self.evaluate_day(day)

    def _write_progress(self, habit_id: int, day: str, value: float) -> None:
        with self.database.connection() as connection:
            habit = connection.execute("SELECT * FROM habits WHERE id = ?", (habit_id,)).fetchone()
            if habit is None:
                raise ValueError(f"Habit {habit_id} does not exist")
            completed = int(value >= float(habit["goal_amount"]))
            connection.execute(
                """
                INSERT INTO daily_habit_progress(habit_id, date, value, completed, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(habit_id, date) DO UPDATE SET
                    value = excluded.value,
                    completed = excluded.completed,
                    updated_at = excluded.updated_at
                """,
                (habit_id, day, value, completed, datetime.now().isoformat(timespec="seconds")),
            )

    def evaluate_day(self, day: str | None = None) -> dict[str, float | int | bool]:
        day = day or today_iso()
        habits = self.get_habits()
        progress = self.get_progress_map(day)
        required = [habit for habit in habits if habit.required]
        required_completed = sum(
            1 for habit in required if progress.get(habit.id, {}).get("completed", False)
        )
        all_completed = bool(required) and required_completed == len(required)
        percentage = (required_completed / len(required) * 100) if required else 100.0

        with self.database.connection() as connection:
            connection.execute(
                """
                INSERT INTO daily_completion(date, completed, completion_percentage, completed_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    completed = excluded.completed,
                    completion_percentage = excluded.completion_percentage,
                    completed_at = CASE
                        WHEN excluded.completed = 1 AND daily_completion.completed_at IS NULL
                        THEN excluded.completed_at
                        ELSE daily_completion.completed_at
                    END
                """,
                (
                    day,
                    int(all_completed),
                    round(percentage, 2),
                    datetime.now().isoformat(timespec="seconds") if all_completed else None,
                ),
            )

        self.streaks.recalculate()
        return {
            "required_total": len(required),
            "required_completed": required_completed,
            "percentage": percentage,
            "day_completed": all_completed,
        }

    def dashboard_snapshot(self) -> dict:
        habits = self.get_habits()
        progress = self.get_progress_map()
        day = self.evaluate_day()
        return {"habits": habits, "progress": progress, **day}
