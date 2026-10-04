from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Iterator

from app.utils.constants import STARTER_HABITS


class Database:
    """Small SQLite gateway. All app persistence flows through this class."""

    def __init__(self, filename: str = "arc_tracker.db") -> None:
        storage_root = os.getenv("FLET_APP_STORAGE_DATA")
        if storage_root:
            data_dir = Path(storage_root)
        else:
            data_dir = Path.home() / ".arc_tracker"
        data_dir.mkdir(parents=True, exist_ok=True)
        self.path = data_dir / filename

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
                    created_at TEXT NOT NULL
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
                    completed_at TEXT
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
                    unlocked INTEGER NOT NULL DEFAULT 0,
                    unlocked_at TEXT
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )

            user_count = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            if user_count == 0:
                connection.execute(
                    "INSERT INTO users(name, journey_start_date, created_at) VALUES (?, ?, ?)",
                    ("Nityansh", date.today().isoformat(), datetime.now().isoformat(timespec="seconds")),
                )

            habit_count = connection.execute("SELECT COUNT(*) FROM habits").fetchone()[0]
            if habit_count == 0:
                for habit in STARTER_HABITS:
                    connection.execute(
                        """
                        INSERT INTO habits(
                            name, icon, category, goal_type, goal_amount,
                            unit, required, schedule, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            habit["name"], habit["icon"], habit["category"],
                            habit["goal_type"], habit["goal_amount"], habit["unit"],
                            habit["required"], habit["schedule"],
                            datetime.now().isoformat(timespec="seconds"),
                        ),
                    )

            connection.execute(
                "INSERT OR IGNORE INTO streaks(id, current_streak, longest_streak, total_completed_days) VALUES (1, 0, 0, 0)"
            )
