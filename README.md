# ARC — Daily Life Tracker

ARC is an offline-first self-improvement app built with Python, Flet, SQLite and Supabase.

## ARC 1.0 RC1

ARC now has a complete public-to-private product flow:

- Public feature preview before account creation
- Email/password signup and login with Supabase Auth
- Secure Android session persistence
- Private per-user cloud data with Row Level Security
- Offline SQLite tracking with Supabase cloud backup
- Automatic cloud restore when a user signs in on another device
- Existing beta data adoption for the first account after upgrading
- Free account plan today with server-controlled premium readiness for later
- Logout, manual sync and cloud status in Profile

The tracker itself includes:

- first-launch onboarding
- boolean and numeric habits
- custom habits, editing, schedules, archive and restore
- required vs optional goals
- perfect-day engine
- streaks, XP, levels and achievements
- calendar history
- weekly/monthly analytics
- weekly self-improvement report
- offline persistence and missed-day handling

## Security model

The APK contains only the Supabase project URL and publishable client key. It never contains a secret or service-role key.

ARC cloud tables use Row Level Security so authenticated users can only access their own rows. The account `plan` column is not updateable by the mobile client; future premium upgrades must come from a trusted backend/admin path.

Auth refresh tokens are stored using Flet SecureStorage, backed by Android Keystore.

## Run locally

```bash
python -m venv .venv
# activate it
pip install -r requirements.txt
flet run main.py
```

## Tests

```bash
python -m compileall -q app main.py
python -m unittest discover -s tests -v
```

## Android

```bash
flet build apk --yes --build-version 1.0.0 --build-number 10
```

A GitHub Actions workflow also produces an installable release-candidate APK artifact.

## Before public release

Supabase Security Advisor currently reports one project-wide Auth recommendation: enable leaked-password protection in the Supabase Auth dashboard. ARC table RLS and performance checks are otherwise clean.
