from __future__ import annotations

from datetime import date, datetime

from app.models.habit import Habit
from app.services.database import Database
from app.services.streak_service import StreakService
from app.services.xp_service import XpService
from app.utils.constants import HABIT_CATEGORIES, WEEKDAY_CODES
from app.utils.dates import today_iso


class HabitService:
    def __init__(self, database: Database) -> None:
        self.database = database
        self.streaks = StreakService(database)
        self.xp = XpService(database)

    def get_all_habits(self, active_only: bool | None = True) -> list[Habit]:
        query = "SELECT * FROM habits"
        if active_only is True:
            query += " WHERE active = 1"
        elif active_only is False:
            query += " WHERE active = 0"
        query += " ORDER BY active DESC, required DESC, id ASC"
        with self.database.connection() as connection:
            rows = connection.execute(query).fetchall()
        return [Habit.from_row(row) for row in rows]

    def get_habit(self, habit_id: int) -> Habit:
        with self.database.connection() as connection:
            row = connection.execute("SELECT * FROM habits WHERE id = ?", (habit_id,)).fetchone()
        if row is None:
            raise ValueError(f"Habit {habit_id} does not exist")
        return Habit.from_row(row)

    def get_habits(self, day: str | date | None = None, include_archived_history: bool = False) -> list[Habit]:
        target_day = date.today() if day is None else day if isinstance(day, date) else date.fromisoformat(day)
        pool = self.get_all_habits(active_only=None if include_archived_history else True)
        result: list[Habit] = []
        for habit in pool:
            if not habit.scheduled_for(target_day) or not habit.existed_on(target_day):
                continue
            if habit.active or include_archived_history:
                result.append(habit)
        return result

    def create_habit(
        self,
        *,
        name: str,
        category: str,
        goal_type: str,
        goal_amount: float,
        unit: str,
        required: bool,
        schedule: str,
        icon: str = "check_circle",
    ) -> int:
        fields = self._validate_habit_fields(
            name=name,
            category=category,
            goal_type=goal_type,
            goal_amount=goal_amount,
            unit=unit,
            schedule=schedule,
        )
        clean_name, clean_category, clean_type, clean_amount, clean_unit, clean_schedule = fields
        now = datetime.now().isoformat(timespec="seconds")
        with self.database.connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO habits(
                    name, icon, category, goal_type, goal_amount,
                    unit, required, schedule, active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    clean_name, icon or "check_circle", clean_category, clean_type,
                    clean_amount, clean_unit, int(required), clean_schedule, now, now,
                ),
            )
            habit_id = int(cursor.lastrowid)
        self.evaluate_day()
        return habit_id

    def update_habit(
        self,
        habit_id: int,
        *,
        name: str,
        category: str,
        goal_type: str,
        goal_amount: float,
        unit: str,
        required: bool,
        schedule: str,
    ) -> None:
        self.get_habit(habit_id)
        fields = self._validate_habit_fields(
            name=name,
            category=category,
            goal_type=goal_type,
            goal_amount=goal_amount,
            unit=unit,
            schedule=schedule,
        )
        clean_name, clean_category, clean_type, clean_amount, clean_unit, clean_schedule = fields
        now = datetime.now().isoformat(timespec="seconds")
        with self.database.connection() as connection:
            connection.execute(
                """
                UPDATE habits
                SET name = ?, category = ?, goal_type = ?, goal_amount = ?,
                    unit = ?, required = ?, schedule = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    clean_name, clean_category, clean_type, clean_amount, clean_unit,
                    int(required), clean_schedule, now, habit_id,
                ),
            )
            progress = connection.execute(
                "SELECT value FROM daily_habit_progress WHERE habit_id = ? AND date = ?",
                (habit_id, today_iso()),
            ).fetchone()
            if progress is not None:
                completed = int(float(progress["value"]) >= clean_amount)
                connection.execute(
                    """
                    UPDATE daily_habit_progress
                    SET completed = ?, updated_at = ?
                    WHERE habit_id = ? AND date = ?
                    """,
                    (completed, now, habit_id, today_iso()),
                )
        self.evaluate_day()

    def archive_habit(self, habit_id: int) -> None:
        self.get_habit(habit_id)
        now = datetime.now().isoformat(timespec="seconds")
        with self.database.connection() as connection:
            connection.execute(
                "UPDATE habits SET active = 0, archived_at = ?, updated_at = ? WHERE id = ?",
                (now, now, habit_id),
            )
        self.evaluate_day()

    def restore_habit(self, habit_id: int) -> None:
        self.get_habit(habit_id)
        now = datetime.now().isoformat(timespec="seconds")
        with self.database.connection() as connection:
            connection.execute(
                "UPDATE habits SET active = 1, archived_at = NULL, updated_at = ? WHERE id = ?",
                (now, habit_id),
            )
        self.evaluate_day()

    def delete_habit_permanently(self, habit_id: int) -> None:
        self.get_habit(habit_id)
        with self.database.connection() as connection:
            connection.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
        self.evaluate_day()

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

    def toggle_boolean(self, habit_id: int, day: str | None = None) -> dict[str, float | int | bool]:
        day = day or today_iso()
        habit = self.get_habit(habit_id)
        if habit.goal_type != "boolean":
            raise ValueError("Only boolean habits can be toggled")
        progress = self.get_progress_map(day).get(habit_id, {"completed": False})
        new_value = 0 if progress["completed"] else 1
        self._write_progress(habit_id, day, new_value)
        return self.evaluate_day(day)

    def increment(self, habit_id: int, amount: float, day: str | None = None) -> dict[str, float | int | bool]:
        day = day or today_iso()
        habit = self.get_habit(habit_id)
        if habit.goal_type != "number":
            raise ValueError("Only number-based habits can be incremented")
        progress = self.get_progress_map(day).get(habit_id, {"value": 0.0})
        self._write_progress(habit_id, day, max(0, float(progress["value"]) + amount))
        return self.evaluate_day(day)

    def set_value(self, habit_id: int, value: float, day: str | None = None) -> dict[str, float | int | bool]:
        day = day or today_iso()
        habit = self.get_habit(habit_id)
        if habit.goal_type != "number":
            raise ValueError("Only number-based habits accept numeric values")
        self._write_progress(habit_id, day, max(0, value))
        return self.evaluate_day(day)

    def _write_progress(self, habit_id: int, day: str, value: float) -> None:
        with self.database.connection() as connection:
            habit = connection.execute("SELECT * FROM habits WHERE id = ?", (habit_id,)).fetchone()
            if habit is None:
                raise ValueError(f"Habit {habit_id} does not exist")
            previous = connection.execute(
                "SELECT completed FROM daily_habit_progress WHERE habit_id = ? AND date = ?",
                (habit_id, day),
            ).fetchone()
            was_completed = bool(previous["completed"]) if previous else False
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
        if completed and not was_completed:
            self.xp.award_once(f"habit:{day}:{habit_id}", 10)

    def evaluate_day(self, day: str | None = None) -> dict[str, float | int | bool]:
        day = day or today_iso()
        habits = self.get_habits(day)
        progress = self.get_progress_map(day)
        required = [habit for habit in habits if habit.required]
        required_completed = sum(
            1 for habit in required if progress.get(habit.id, {}).get("completed", False)
        )
        all_completed = bool(required) and required_completed == len(required)
        percentage = (required_completed / len(required) * 100) if required else 0.0
        now = datetime.now().isoformat(timespec="seconds")

        with self.database.connection() as connection:
            existing = connection.execute(
                "SELECT completed, completed_at FROM daily_completion WHERE date = ?",
                (day,),
            ).fetchone()
            ever_completed = bool(existing and existing["completed_at"])
            completed_at = existing["completed_at"] if ever_completed else now if all_completed else None
            connection.execute(
                """
                INSERT INTO daily_completion(
                    date, completed, completion_percentage, scheduled_required,
                    completed_required, completed_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    completed = excluded.completed,
                    completion_percentage = excluded.completion_percentage,
                    scheduled_required = excluded.scheduled_required,
                    completed_required = excluded.completed_required,
                    completed_at = COALESCE(daily_completion.completed_at, excluded.completed_at),
                    updated_at = excluded.updated_at
                """,
                (
                    day, int(all_completed), round(percentage, 2), len(required),
                    required_completed, completed_at, now,
                ),
            )

        newly_completed = all_completed and not ever_completed
        if newly_completed:
            self.xp.award_once(f"perfect_day:{day}", 100)
        self.streaks.recalculate()

        from app.services.achievement_service import AchievementService
        AchievementService(self.database).sync()

        return {
            "required_total": len(required),
            "required_completed": required_completed,
            "percentage": percentage,
            "day_completed": all_completed,
            "newly_completed": newly_completed,
        }

    def dashboard_snapshot(self) -> dict:
        habits = self.get_habits()
        progress = self.get_progress_map()
        day = self.evaluate_day()
        return {"habits": habits, "progress": progress, **day}

    @staticmethod
    def _validate_habit_fields(
        *,
        name: str,
        category: str,
        goal_type: str,
        goal_amount: float,
        unit: str,
        schedule: str,
    ) -> tuple[str, str, str, float, str, str]:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Habit name is required")
        if len(clean_name) > 60:
            raise ValueError("Habit name must be 60 characters or fewer")

        clean_category = category.strip() or "Custom"
        if clean_category not in HABIT_CATEGORIES:
            clean_category = "Custom"

        clean_type = goal_type.strip().lower()
        if clean_type not in {"boolean", "number"}:
            raise ValueError("Goal type must be boolean or number")

        clean_amount = 1.0 if clean_type == "boolean" else float(goal_amount)
        if clean_amount <= 0:
            raise ValueError("Goal amount must be greater than zero")

        clean_unit = (unit.strip() or "unit") if clean_type == "number" else "completion"

        clean_schedule = schedule.strip().lower()
        if clean_schedule != "daily":
            selected = [part for part in clean_schedule.split(",") if part in WEEKDAY_CODES]
            selected = list(dict.fromkeys(selected))
            if not selected:
                raise ValueError("Choose at least one day")
            clean_schedule = "daily" if len(selected) == 7 else ",".join(selected)

        return clean_name, clean_category, clean_type, clean_amount, clean_unit, clean_schedule
