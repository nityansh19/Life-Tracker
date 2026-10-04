# ARC — Daily Life Tracker

ARC is a premium, offline-first self-improvement tracker built with Python, Flet, and SQLite.

## Current build

- Dark-first mobile UI
- Home, Calendar, Progress, Achievements, and Profile tabs
- SQLite persistence
- Database-driven starter habits
- Boolean and numeric habit tracking
- Custom habit creation
- Habit editing
- Required vs optional habits
- Daily or selected-weekday schedules
- Habit archive/restore with history preservation
- Optional permanent deletion with an explicit warning
- Schedule-aware daily completion percentage
- Perfect-day persistence
- Current and longest streak calculation
- Basic history and analytics
- Modular architecture ready for cloud sync later

## Habit scheduling

Schedules are stored locally as either:

- `daily`
- weekday codes such as `mon,wed,fri`

Only habits scheduled for the current day appear on the Home dashboard. Only required habits scheduled for that day affect perfect-day completion and streaks.

## Run locally

1. `python -m venv .venv`
2. Activate the environment
3. `pip install -r requirements.txt`
4. `flet run main.py`

## Android build

```bash
flet build apk
```

Status: active development — custom habit management and schedule-aware tracking are implemented.
