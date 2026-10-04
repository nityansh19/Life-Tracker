from __future__ import annotations

from datetime import date

from app.services.database import Database


class UserService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def get(self) -> dict:
        with self.database.connection() as connection:
            row = connection.execute("SELECT * FROM users ORDER BY id LIMIT 1").fetchone()
        return dict(row)

    def update_profile(self, name: str, journey_start_date: str | None = None) -> None:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Name is required")
        if len(clean_name) > 40:
            raise ValueError("Name must be 40 characters or fewer")
        with self.database.connection() as connection:
            row = connection.execute("SELECT id, journey_start_date FROM users ORDER BY id LIMIT 1").fetchone()
            start = journey_start_date or row["journey_start_date"]
            parsed = date.fromisoformat(start)
            if parsed > date.today():
                raise ValueError("Journey start date cannot be in the future")
            connection.execute(
                "UPDATE users SET name = ?, journey_start_date = ? WHERE id = ?",
                (clean_name, parsed.isoformat(), row["id"]),
            )
