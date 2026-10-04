from __future__ import annotations

from datetime import date, timedelta

from app.services.database import Database
from app.services.xp_service import XpService


class StreakService:
    """Derives streaks from persisted perfect-day rows, never from cached counters."""

    def __init__(self, database: Database) -> None:
        self.database = database
        self.xp = XpService(database)

    def recalculate(self) -> dict[str, int | str | None]:
        with self.database.connection() as connection:
            rows = connection.execute(
                "SELECT date FROM daily_completion WHERE completed = 1 ORDER BY date ASC"
            ).fetchall()
            completed_dates = [date.fromisoformat(row["date"]) for row in rows]
            completed_set = set(completed_dates)

            current = 0
            today = date.today()
            anchor = today if today in completed_set else today - timedelta(days=1)
            while anchor in completed_set:
                current += 1
                anchor -= timedelta(days=1)

            longest = 0
            running = 0
            previous: date | None = None
            for completed_date in completed_dates:
                running = running + 1 if previous and completed_date == previous + timedelta(days=1) else 1
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

        if current >= 7:
            self.xp.award_once("streak:7", 250)

        return {
            "current_streak": current,
            "longest_streak": longest,
            "total_completed_days": len(completed_dates),
            "last_completed_date": last_completed,
        }

    def snapshot(self) -> dict[str, int | str | None]:
        return self.recalculate()
