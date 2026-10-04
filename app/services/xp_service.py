from __future__ import annotations

from datetime import datetime

from app.services.database import Database


class XpService:
    XP_PER_LEVEL = 250

    def __init__(self, database: Database) -> None:
        self.database = database

    def award_once(self, event_key: str, amount: int) -> bool:
        if amount <= 0:
            return False
        with self.database.connection() as connection:
            exists = connection.execute(
                "SELECT 1 FROM xp_events WHERE event_key = ?",
                (event_key,),
            ).fetchone()
            if exists:
                return False
            connection.execute(
                "INSERT INTO xp_events(event_key, amount, created_at) VALUES (?, ?, ?)",
                (event_key, amount, datetime.now().isoformat(timespec="seconds")),
            )
            row = connection.execute("SELECT id, xp FROM users ORDER BY id LIMIT 1").fetchone()
            new_xp = int(row["xp"]) + amount
            new_level = self.level_for_xp(new_xp)
            connection.execute(
                "UPDATE users SET xp = ?, level = ? WHERE id = ?",
                (new_xp, new_level, row["id"]),
            )
        return True

    @classmethod
    def level_for_xp(cls, xp: int) -> int:
        return max(1, 1 + int(xp) // cls.XP_PER_LEVEL)

    @staticmethod
    def title_for_level(level: int) -> str:
        if level >= 50:
            return "Unstoppable"
        if level >= 20:
            return "Locked In"
        if level >= 10:
            return "Disciplined"
        if level >= 5:
            return "Consistent"
        return "Starter"

    def snapshot(self) -> dict[str, int | str | float]:
        with self.database.connection() as connection:
            row = connection.execute("SELECT xp, level FROM users ORDER BY id LIMIT 1").fetchone()
        xp = int(row["xp"])
        level = int(row["level"])
        current_floor = (level - 1) * self.XP_PER_LEVEL
        progress = (xp - current_floor) / self.XP_PER_LEVEL
        return {
            "xp": xp,
            "level": level,
            "title": self.title_for_level(level),
            "level_progress": min(max(progress, 0), 1),
            "xp_to_next": self.XP_PER_LEVEL - (xp - current_floor),
        }
