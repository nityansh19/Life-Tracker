from dataclasses import dataclass


@dataclass(slots=True)
class DailyProgress:
    habit_id: int
    date: str
    value: float
    completed: bool
