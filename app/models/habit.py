from __future__ import annotations

from dataclasses import dataclass


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
