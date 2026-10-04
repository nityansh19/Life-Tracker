# ARC — Daily Life Tracker

ARC is a premium, offline-first self-improvement tracker built with Python, Flet, and SQLite.

Current build:
- Dark-first mobile UI
- Home, Calendar, Progress, Achievements, and Profile tabs
- SQLite persistence
- Database-driven starter habits
- Boolean and numeric habit tracking
- Required vs optional habit logic
- Daily completion percentage
- Perfect-day persistence
- Current and longest streak calculation
- Basic history and analytics
- Modular architecture ready for cloud sync later

Run locally:
1. python -m venv .venv
2. Activate the environment
3. pip install -r requirements.txt
4. flet run main.py

Android build:
flet build apk

Status: active development — core architecture and daily tracking engine are in place.
