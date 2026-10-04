from __future__ import annotations

from app.services.database import Database


class SettingsService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def get(self, key: str, default: str | None = None) -> str | None:
        with self.database.connection() as connection:
            row = connection.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def set(self, key: str, value: str | int | float | bool) -> None:
        normalized = "1" if value is True else "0" if value is False else str(value)
        with self.database.connection() as connection:
            connection.execute(
                """
                INSERT INTO settings(key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, normalized),
            )

    def get_bool(self, key: str, default: bool = False) -> bool:
        value = self.get(key)
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "on"}
