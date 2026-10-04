from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.utils.constants import WEEKDAY_CODES, WEEKDAY_LABELS


@dataclass(slots=True)
class Habit:
    id: int
    name: str
    icon: str
    category: str
    goal_type: str
    goal_amount: float
    unit: str
    required: bool
    schedule: str
    active: bool

    @classmethod
    def from_row(cls, row) -> "Habit":
        return cls(
            id=row["id"],
            name=row["name"],
            icon=row["icon"],
            category=row["category"],
            goal_type=row["goal_type"],
            goal_amount=float(row["goal_amount"]),
            unit=row["unit"],
            required=bool(row["required"]),
            schedule=row["schedule"],
            active=bool(row["active"]),
        )

    def scheduled_for(self, day: date) -> bool:
        if self.schedule == "daily":
            return True
        selected = {part.strip().lower() for part in self.schedule.split(",") if part.strip()}
        return WEEKDAY_CODES[day.weekday()] in selected

    @property
    def schedule_label(self) -> str:
        if self.schedule == "daily":
            return "Every day"
        selected = {part.strip().lower() for part in self.schedule.split(",") if part.strip()}
        labels = [
            label
            for code, label in zip(WEEKDAY_CODES, WEEKDAY_LABELS)
            if code in selected
        ]
        return ", ".join(labels) if labels else "No days"
