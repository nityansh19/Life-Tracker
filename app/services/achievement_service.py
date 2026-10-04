from __future__ import annotations

from datetime import datetime

from app.services.database import Database
from app.services.streak_service import StreakService
from app.services.xp_service import XpService


ACHIEVEMENTS = (
    ("first_flame", "First Flame", "Complete your first perfect day"),
    ("week_strong", "One Week Strong", "Reach a 7-day streak"),
    ("locked_in", "Locked In", "Reach a 14-day streak"),
    ("discipline", "Discipline", "Reach a 30-day streak"),
    ("unstoppable", "Unstoppable", "Reach a 100-day streak"),
    ("100k_club", "100K Club", "Walk 100,000 total steps"),
    ("hydrated", "Hydrated", "Complete your water goal 30 times"),
    ("scholar", "Scholar", "Study for 50 total hours"),
    ("consistent", "Consistent", "Complete 50 workouts"),
)


class AchievementService:
    def __init__(self, database: Database) -> None:
        self.database = database
        self.xp = XpService(database)
        self._seed()

    def _seed(self) -> None:
        with self.database.connection() as connection:
            for key, title, description in ACHIEVEMENTS:
                connection.execute(
                    """
                    INSERT INTO achievements(key, title, description, unlocked)
                    VALUES (?, ?, ?, 0)
                    ON CONFLICT(key) DO UPDATE SET
                        title = excluded.title,
                        description = excluded.description
                    """,
                    (key, title, description),
                )

    def sync(self) -> list[str]:
        streak = StreakService(self.database).snapshot()
        with self.database.connection() as connection:
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
            water_days = int(
                connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM daily_habit_progress p
                    JOIN habits h ON h.id = p.habit_id
                    WHERE p.completed = 1 AND (LOWER(h.unit) = 'ml' OR LOWER(h.name) LIKE '%water%')
                    """
                ).fetchone()[0]
            )
            study_minutes = float(
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

        eligible = {
            "first_flame": int(streak["total_completed_days"]) >= 1,
            "week_strong": int(streak["longest_streak"]) >= 7,
            "locked_in": int(streak["longest_streak"]) >= 14,
            "discipline": int(streak["longest_streak"]) >= 30,
            "unstoppable": int(streak["longest_streak"]) >= 100,
            "100k_club": total_steps >= 100000,
            "hydrated": water_days >= 30,
            "scholar": study_minutes >= 3000,
            "consistent": workouts >= 50,
        }

        unlocked_now: list[str] = []
        with self.database.connection() as connection:
            for key, should_unlock in eligible.items():
                if not should_unlock:
                    continue
                row = connection.execute(
                    "SELECT unlocked FROM achievements WHERE key = ?",
                    (key,),
                ).fetchone()
                if row and not bool(row["unlocked"]):
                    connection.execute(
                        "UPDATE achievements SET unlocked = 1, unlocked_at = ? WHERE key = ?",
                        (datetime.now().isoformat(timespec="seconds"), key),
                    )
                    unlocked_now.append(key)

        for key in unlocked_now:
            self.xp.award_once(f"achievement:{key}", 50)
        return unlocked_now

    def list_all(self) -> list[dict]:
        self.sync()
        with self.database.connection() as connection:
            rows = connection.execute(
                "SELECT key, title, description, unlocked, unlocked_at FROM achievements ORDER BY rowid"
            ).fetchall()
        return [dict(row) for row in rows]
