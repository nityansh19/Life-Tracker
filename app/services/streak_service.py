from __future__ import annotations

from datetime import date, timedelta

from app.services.database import Database


class StreakService:
    """Derives streaks from persisted perfect-day records to avoid double counting."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def recalculate(self) -> dict[str, int | str | None]:
        with self.database.connection() as connection:
            rows = connection.execute(
                "SELECT date FROM daily_completion WHERE completed = 1 ORDER BY date ASC"
            ).fetchall()

            completed_dates = [date.fromisoformat(row["date"]) for row in rows]
            completed_set = set(completed_dates)

            current = 0
            anchor = date.today() if date.today() in completed_set else date.today() - timedelta(days=1)
            while anchor in completed_set:
                current += 1
                anchor -= timedelta(days=1)

            longest = 0
            running = 0
            previous = None
            for completed_date in completed_dates:
                if previous and completed_date == previous + timedelta(days=1):
                    running += 1
                else:
                    running = 1
                longest = max(longest, running)
                previous = completed_date

            last_completed = completed_dates[-1].isoformat() if completed_dates else None
            connection.execute(
                """
                UPDATE streaks
                SET current_streak = ?, longest_streak = ?, total_completed_days = ?, last_completed_date = ?
                WHERE id = 1
                """,
                (current, longest, len(completed_dates), last_completed),
            )
            return {
                "current_streak": current,
                "longest_streak": longest,
                "total_completed_days": len(completed_dates),
                "last_completed_date": last_completed,
            }

    def snapshot(self) -> dict[str, int | str | None]:
        return self.recalculate()
