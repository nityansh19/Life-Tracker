from dataclasses import dataclass


@dataclass(slots=True)
class User:
    id: int
    name: str
    journey_start_date: str
    xp: int
    level: int
