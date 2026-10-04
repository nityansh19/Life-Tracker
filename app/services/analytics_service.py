from __future__ import annotations

from datetime import date, timedelta

from app.services.database import Database
from app.services.day_service import DayService
from app.services.streak_service import StreakService


class AnalyticsService:
    def __init__(self, database: Database) -> None:
        self.database = database
        self.days = DayService(database)

    def completion_rate(self, days: int) -> float:
        self.days.sync_history()
        start = (date.today() - timedelta(days=max(days - 1, 0))).isoformat()
        with self.database.connection() as connection:
            row = connection.execute(
                "SELECT AVG(completion_percentage) AS average FROM daily_completion WHERE date >= ? AND date <= ?",
                (start, date.today().isoformat()),
            ).fetchone()
        return round(float(row["average"] or 0), 1)

    def totals(self) -> dict[str, float | int]:
        self.days.sync_history()
        today = date.today().isoformat()
        with self.database.connection() as connection:
            perfect_days = connection.execute(
                "SELECT COUNT(*) FROM daily_completion WHERE completed = 1"
            ).fetchone()[0]
            missed_days = connection.execute(
                "SELECT COUNT(*) FROM daily_completion WHERE completed = 0 AND date < ?",
                (today,),
            ).fetchone()[0]
            completed_habits = connection.execute(
                "SELECT COUNT(*) FROM daily_habit_progress WHERE completed = 1"
            ).fetchone()[0]
            total_steps = float(
                connection.execute(
                    """
                    SELECT COALESCE(SUM(p.value), 0)
                    FROM daily_habit_progress p
                    JOIN habits h ON h.id = p.habit_id
                    WHERE LOWER(h.unit) = 'steps'
                    """
                ).fetchone()[0]
            )
            total_study_minutes = float(
                connection.execute(
                    """
                    SELECT COALESCE(SUM(p.value), 0)
                    FROM daily_habit_progress p
                    JOIN habits h ON h.id = p.habit_id
                    WHERE LOWER(h.unit) = 'minutes' AND LOWER(h.category) = 'study'
                    """
                ).fetchone()[0]
            )
            workouts = int(
                connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM daily_habit_progress p
                    JOIN habits h ON h.id = p.habit_id
                    WHERE p.completed = 1 AND LOWER(h.name) LIKE '%workout%'
                    """
                ).fetchone()[0]
            )
        return {
            "perfect_days": int(perfect_days),
            "missed_days": int(missed_days),
            "completed_habits": int(completed_habits),
            "total_steps": int(total_steps),
            "total_study_minutes": int(total_study_minutes),
            "total_workouts": workouts,
        }

    def averages(self, days: int = 7) -> dict[str, float]:
        start = (date.today() - timedelta(days=max(days - 1, 0))).isoformat()
        end = date.today().isoformat()
        with self.database.connection() as connection:
            values: dict[str, float] = {}
            for unit, key in (("steps", "steps"), ("ml", "water_ml")):
                row = connection.execute(
                    """
                    SELECT AVG(day_total) AS average FROM (
                        SELECT p.date, SUM(p.value) AS day_total
                        FROM daily_habit_progress p
                        JOIN habits h ON h.id = p.habit_id
                        WHERE LOWER(h.unit) = ? AND p.date BETWEEN ? AND ?
                        GROUP BY p.date
                    )
                    """,
                    (unit, start, end),
                ).fetchone()
                values[key] = round(float(row["average"] or 0), 1)

            study = connection.execute(
                """
                SELECT AVG(day_total) AS average FROM (
                    SELECT p.date, SUM(p.value) AS day_total
                    FROM daily_habit_progress p
                    JOIN habits h ON h.id = p.habit_id
                    WHERE LOWER(h.unit) = 'minutes' AND LOWER(h.category) = 'study'
                      AND p.date BETWEEN ? AND ?
                    GROUP BY p.date
                )
                """,
                (start, end),
            ).fetchone()
            values["study_minutes"] = round(float(study["average"] or 0), 1)
        return values

    def workout_consistency(self, days: int = 30) -> float:
        start_day = date.today() - timedelta(days=max(days - 1, 0))
        planned = 0
        completed = 0
        cursor = start_day
        while cursor <= date.today():
            workouts = [
                habit for habit in self.days.habits.get_habits(cursor)
                if "workout" in habit.name.lower()
            ]
            if workouts:
                planned += len(workouts)
                progress = self.days.habits.get_progress_map(cursor.isoformat())
                completed += sum(1 for habit in workouts if progress.get(habit.id, {}).get("completed", False))
            cursor += timedelta(days=1)
        return round((completed / planned * 100) if planned else 0.0, 1)

    def weekly_report(self, anchor: date | None = None) -> dict:
        self.days.sync_history()
        anchor = anchor or date.today()
        current_start = anchor - timedelta(days=anchor.weekday())
        current_end = anchor
        elapsed = (current_end - current_start).days
        previous_start = current_start - timedelta(days=7)
        previous_end = previous_start + timedelta(days=elapsed)

        current = self._range_report(current_start, current_end)
        previous = self._range_report(previous_start, previous_end)
        delta = round(current["completion_percentage"] - previous["completion_percentage"], 1)
        if delta > 0:
            message = f"You improved your consistency by {delta:g}% compared with last week."
        elif delta < 0:
            message = f"Consistency is {abs(delta):g}% lower than last week. Finish strong."
        else:
            message = "Your consistency matches last week. One extra perfect day moves the needle."

        current["comparison_delta"] = delta
        current["message"] = message
        current["current_streak"] = int(StreakService(self.database).snapshot()["current_streak"])
        return current

    def _range_report(self, start: date, end: date) -> dict:
        start_iso, end_iso = start.isoformat(), end.isoformat()
        with self.database.connection() as connection:
            summary = connection.execute(
                """
                SELECT AVG(completion_percentage) AS average, SUM(completed) AS perfect_days
                FROM daily_completion
                WHERE date BETWEEN ? AND ?
                """,
                (start_iso, end_iso),
            ).fetchone()
            workout = connection.execute(
                """
                SELECT COUNT(*) AS completed
                FROM daily_habit_progress p
                JOIN habits h ON h.id = p.habit_id
                WHERE p.completed = 1 AND LOWER(h.name) LIKE '%workout%'
                  AND p.date BETWEEN ? AND ?
                """,
                (start_iso, end_iso),
            ).fetchone()[0]
            avg_steps = connection.execute(
                """
                SELECT AVG(day_total) FROM (
                    SELECT p.date, SUM(p.value) AS day_total
                    FROM daily_habit_progress p
                    JOIN habits h ON h.id = p.habit_id
                    WHERE LOWER(h.unit) = 'steps' AND p.date BETWEEN ? AND ?
                    GROUP BY p.date
                )
                """,
                (start_iso, end_iso),
            ).fetchone()[0]
            avg_water = connection.execute(
                """
                SELECT AVG(day_total) FROM (
                    SELECT p.date, SUM(p.value) AS day_total
                    FROM daily_habit_progress p
                    JOIN habits h ON h.id = p.habit_id
                    WHERE LOWER(h.unit) = 'ml' AND p.date BETWEEN ? AND ?
                    GROUP BY p.date
                )
                """,
                (start_iso, end_iso),
            ).fetchone()[0]
            study = connection.execute(
                """
                SELECT COALESCE(SUM(p.value), 0)
                FROM daily_habit_progress p
                JOIN habits h ON h.id = p.habit_id
                WHERE LOWER(h.unit) = 'minutes' AND LOWER(h.category) = 'study'
                  AND p.date BETWEEN ? AND ?
                """,
                (start_iso, end_iso),
            ).fetchone()[0]
        return {
            "start": start_iso,
            "end": end_iso,
            "completion_percentage": round(float(summary["average"] or 0), 1),
            "perfect_days": int(summary["perfect_days"] or 0),
            "workouts": int(workout or 0),
            "average_steps": int(round(float(avg_steps or 0))),
            "average_water_ml": int(round(float(avg_water or 0))),
            "study_minutes": int(round(float(study or 0))),
        }
