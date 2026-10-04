from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Iterator

from app.utils.constants import APP_VERSION, STARTER_HABITS


class Database:
    """SQLite gateway with migrations plus cloud snapshot import/export."""

    SNAPSHOT_TABLES = (
        "users",
        "habits",
        "daily_habit_progress",
        "daily_completion",
        "streaks",
        "achievements",
        "settings",
        "xp_events",
    )

    def __init__(self, filename: str = "arc_tracker.db", data_dir: str | Path | None = None) -> None:
        if data_dir is not None:
            root = Path(data_dir)
        else:
            storage_root = os.getenv("FLET_APP_STORAGE_DATA")
            root = Path(storage_root) if storage_root else Path.home() / ".arc_tracker"
        root.mkdir(parents=True, exist_ok=True)
        self.path = root / filename

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    journey_start_date TEXT NOT NULL,
                    xp INTEGER NOT NULL DEFAULT 0,
                    level INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS habits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    icon TEXT NOT NULL DEFAULT 'check_circle',
                    category TEXT NOT NULL DEFAULT 'Custom',
                    goal_type TEXT NOT NULL CHECK(goal_type IN ('boolean', 'number')),
                    goal_amount REAL NOT NULL DEFAULT 1,
                    unit TEXT NOT NULL DEFAULT '',
                    required INTEGER NOT NULL DEFAULT 1,
                    schedule TEXT NOT NULL DEFAULT 'daily',
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    archived_at TEXT
                );

                CREATE TABLE IF NOT EXISTS daily_habit_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    habit_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    value REAL NOT NULL DEFAULT 0,
                    completed INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL,
                    UNIQUE(habit_id, date),
                    FOREIGN KEY(habit_id) REFERENCES habits(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS daily_completion (
                    date TEXT PRIMARY KEY,
                    completed INTEGER NOT NULL DEFAULT 0,
                    completion_percentage REAL NOT NULL DEFAULT 0,
                    scheduled_required INTEGER NOT NULL DEFAULT 0,
                    completed_required INTEGER NOT NULL DEFAULT 0,
                    completed_at TEXT,
                    updated_at TEXT
                );

                CREATE TABLE IF NOT EXISTS streaks (
                    id INTEGER PRIMARY KEY CHECK(id = 1),
                    current_streak INTEGER NOT NULL DEFAULT 0,
                    longest_streak INTEGER NOT NULL DEFAULT 0,
                    total_completed_days INTEGER NOT NULL DEFAULT 0,
                    last_completed_date TEXT
                );

                CREATE TABLE IF NOT EXISTS achievements (
                    key TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    unlocked INTEGER NOT NULL DEFAULT 0,
                    unlocked_at TEXT
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS xp_events (
                    event_key TEXT PRIMARY KEY,
                    amount INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_progress_date ON daily_habit_progress(date);
                CREATE INDEX IF NOT EXISTS idx_progress_habit ON daily_habit_progress(habit_id);
                CREATE INDEX IF NOT EXISTS idx_completion_completed ON daily_completion(completed, date);
                """
            )

            self._ensure_column(connection, "habits", "updated_at", "TEXT")
            self._ensure_column(connection, "habits", "archived_at", "TEXT")
            self._ensure_column(connection, "daily_completion", "scheduled_required", "INTEGER NOT NULL DEFAULT 0")
            self._ensure_column(connection, "daily_completion", "completed_required", "INTEGER NOT NULL DEFAULT 0")
            self._ensure_column(connection, "daily_completion", "updated_at", "TEXT")
            self._ensure_column(connection, "achievements", "description", "TEXT NOT NULL DEFAULT ''")

            now = datetime.now().isoformat(timespec="seconds")
            if connection.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
                connection.execute(
                    "INSERT INTO users(name, journey_start_date, created_at) VALUES (?, ?, ?)",
                    ("Nityansh", date.today().isoformat(), now),
                )

            if connection.execute("SELECT COUNT(*) FROM habits").fetchone()[0] == 0:
                for habit in STARTER_HABITS:
                    connection.execute(
                        """
                        INSERT INTO habits(
                            name, icon, category, goal_type, goal_amount,
                            unit, required, schedule, active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                        """,
                        (
                            habit["name"], habit["icon"], habit["category"],
                            habit["goal_type"], habit["goal_amount"], habit["unit"],
                            habit["required"], habit["schedule"], now, now,
                        ),
                    )

            connection.execute(
                "INSERT OR IGNORE INTO streaks(id, current_streak, longest_streak, total_completed_days) VALUES (1, 0, 0, 0)"
            )
            defaults = {
                "onboarding_complete": "0",
                "reminder_morning": "0",
                "reminder_evening": "0",
                "app_version": APP_VERSION,
            }
            for key, value in defaults.items():
                connection.execute(
                    "INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)",
                    (key, value),
                )
            connection.execute(
                "UPDATE settings SET value = ? WHERE key = 'app_version'",
                (APP_VERSION,),
            )

    def export_state(self) -> dict:
        state: dict[str, list[dict]] = {}
        with self.connection() as connection:
            for table in self.SNAPSHOT_TABLES:
                rows = connection.execute(f"SELECT * FROM {table}").fetchall()
                data = [dict(row) for row in rows]
                if table == "settings":
                    data = [row for row in data if row.get("key") != "cloud_owner_id"]
                state[table] = data
        return state

    def import_state(self, state: dict) -> None:
        if not isinstance(state, dict):
            raise ValueError("Invalid ARC cloud state")

        delete_order = (
            "daily_habit_progress",
            "daily_completion",
            "xp_events",
            "achievements",
            "streaks",
            "habits",
            "users",
            "settings",
        )
        insert_order = (
            "users",
            "habits",
            "daily_habit_progress",
            "daily_completion",
            "streaks",
            "achievements",
            "settings",
            "xp_events",
        )

        with self.connection() as connection:
            connection.execute("PRAGMA foreign_keys = OFF")
            try:
                for table in delete_order:
                    connection.execute(f"DELETE FROM {table}")

                for table in insert_order:
                    rows = state.get(table, [])
                    if not isinstance(rows, list):
                        continue
                    allowed = {
                        row["name"]
                        for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
                    }
                    for raw in rows:
                        if not isinstance(raw, dict):
                            continue
                        row = {key: value for key, value in raw.items() if key in allowed}
                        if not row:
                            continue
                        columns = list(row.keys())
                        placeholders = ", ".join("?" for _ in columns)
                        names = ", ".join(columns)
                        connection.execute(
                            f"INSERT INTO {table} ({names}) VALUES ({placeholders})",
                            tuple(row[column] for column in columns),
                        )
            finally:
                connection.execute("PRAGMA foreign_keys = ON")

        self.initialize()

    def reset_user_state(self) -> None:
        with self.connection() as connection:
            connection.execute("PRAGMA foreign_keys = OFF")
            try:
                for table in (
                    "daily_habit_progress",
                    "daily_completion",
                    "xp_events",
                    "achievements",
                    "streaks",
                    "habits",
                    "users",
                    "settings",
                ):
                    connection.execute(f"DELETE FROM {table}")
            finally:
                connection.execute("PRAGMA foreign_keys = ON")
        self.initialize()

    @staticmethod
    def _ensure_column(connection: sqlite3.Connection, table: str, column: str, declaration: str) -> None:
        columns = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in columns:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {declaration}")
