from __future__ import annotations

from datetime import date, timedelta

from app.services.database import Database
from app.services.habit_service import HabitService


class DayService:
    def __init__(self, database: Database) -> None:
        self.database = database
        self.habits = HabitService(database)

    def journey_start(self) -> date:
        with self.database.connection() as connection:
            row = connection.execute("SELECT journey_start_date FROM users ORDER BY id LIMIT 1").fetchone()
        return date.fromisoformat(row["journey_start_date"])

    def journey_day_number(self, day: date | None = None) -> int:
        day = day or date.today()
        return max(1, (day - self.journey_start()).days + 1)

    def sync_history(self) -> None:
        start = self.journey_start()
        yesterday = date.today() - timedelta(days=1)
        if start > yesterday:
            return
        with self.database.connection() as connection:
            existing = {
                row["date"]
                for row in connection.execute(
                    "SELECT date FROM daily_completion WHERE date >= ? AND date <= ?",
                    (start.isoformat(), yesterday.isoformat()),
                ).fetchall()
            }
        cursor = start
        while cursor <= yesterday:
            if cursor.isoformat() not in existing:
                self.habits.evaluate_day(cursor.isoformat())
            cursor += timedelta(days=1)

    def day_detail(self, day: str | date) -> dict:
        target = day if isinstance(day, date) else date.fromisoformat(day)
        day_iso = target.isoformat()
        progress = self.habits.get_progress_map(day_iso)
        planned = self.habits.get_habits(day_iso, include_archived_history=True)

        with self.database.connection() as connection:
            completion = connection.execute(
                "SELECT * FROM daily_completion WHERE date = ?",
                (day_iso,),
            ).fetchone()

        items = []
        for habit in planned:
            state = progress.get(habit.id, {"value": 0.0, "completed": False})
            items.append(
                {
                    "id": habit.id,
                    "name": habit.name,
                    "category": habit.category,
                    "goal_type": habit.goal_type,
                    "goal_amount": habit.goal_amount,
                    "unit": habit.unit,
                    "required": habit.required,
                    "value": float(state["value"]),
                    "completed": bool(state["completed"]),
                }
            )

        return {
            "date": day_iso,
            "completed": bool(completion["completed"]) if completion else False,
            "percentage": float(completion["completion_percentage"]) if completion else 0.0,
            "scheduled_required": int(completion["scheduled_required"]) if completion else sum(1 for item in items if item["required"]),
            "completed_required": int(completion["completed_required"]) if completion else sum(1 for item in items if item["required"] and item["completed"]),
            "habits": items,
        }

    def recent_days(self, days: int = 30) -> list[dict]:
        self.sync_history()
        start = (date.today() - timedelta(days=days - 1)).isoformat()
        with self.database.connection() as connection:
            rows = connection.execute(
                """
                SELECT date, completed, completion_percentage, scheduled_required, completed_required
                FROM daily_completion
                WHERE date >= ?
                ORDER BY date DESC
                """,
                (start,),
            ).fetchall()
        return [dict(row) for row in rows]
