from __future__ import annotations

from datetime import date, timedelta

from app.services.database import Database


class AnalyticsService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def completion_rate(self, days: int) -> float:
        start = (date.today() - timedelta(days=days - 1)).isoformat()
        with self.database.connection() as connection:
            row = connection.execute(
                """
                SELECT AVG(completion_percentage) AS average
                FROM daily_completion
                WHERE date >= ?
                """,
                (start,),
            ).fetchone()
        return round(float(row["average"] or 0), 1)

    def totals(self) -> dict[str, float | int]:
        with self.database.connection() as connection:
            perfect_days = connection.execute(
                "SELECT COUNT(*) FROM daily_completion WHERE completed = 1"
            ).fetchone()[0]
            missed_days = connection.execute(
                "SELECT COUNT(*) FROM daily_completion WHERE completed = 0"
            ).fetchone()[0]
            completed_habits = connection.execute(
                "SELECT COUNT(*) FROM daily_habit_progress WHERE completed = 1"
            ).fetchone()[0]
        return {
            "perfect_days": int(perfect_days),
            "missed_days": int(missed_days),
            "completed_habits": int(completed_habits),
        }
