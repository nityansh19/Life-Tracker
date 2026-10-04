# ARC — Daily Life Tracker

ARC is a polished offline-first self-improvement app built with Python, Flet, and SQLite. It is designed around a simple loop: open today's mission, complete the habits that matter, protect your streak, inspect your history, and improve your consistency over time.

## Beta feature set

- Premium dark-first mobile UI with five-tab navigation
- First-launch onboarding and starter-goal selection
- Boolean and numeric habits
- Steps, water, study-duration and custom-unit tracking
- Custom habit creation, editing, scheduling, archive/restore and safe deletion
- Required vs optional goals
- Schedule-aware perfect-day engine
- Persistent SQLite history with missed-day backfilling
- Current streak, best streak and perfect-day tracking
- One-time XP awards for completed habits, perfect days, streak milestones and achievements
- Level system with Starter, Consistent, Disciplined, Locked In and Unstoppable ranks
- Detailed current-month calendar and tappable day history
- 7-day / 30-day completion analytics
- Steps, water, study and workout consistency statistics
- Weekly self-improvement report with week-over-week comparison
- Achievement engine for streak, steps, hydration, study and workout milestones
- Today summary and perfect-day celebration flow
- Editable profile and journey start date
- Offline reminder preferences ready for a future native notification integration
- Automated core-engine tests and a manual Android beta build workflow

## Run locally

\`\`\`bash
python -m venv .venv
# activate the environment
pip install -r requirements.txt
flet run main.py
\`\`\`

## Run core tests

\`\`\`bash
python -m unittest discover -s tests -v
python -m compileall -q app main.py
\`\`\`

## Build Android beta

Flet supports Android APK builds on Linux, macOS, and Windows:

\`\`\`bash
flet build apk
\`\`\`

The repository also contains a manually triggered GitHub Actions workflow that builds an APK and uploads it as a workflow artifact for testers.

## Data

ARC is offline-first. User data is stored locally in SQLite. Existing Phase 1/2 databases are upgraded through lightweight schema migrations rather than being replaced.

## Beta status

Version \`0.9.0-beta\` is feature-complete for the first closed testing round. Testing should focus on first launch, habit editing, date rollover, streak behavior, Android layout/orientation, and persistence after force-closing the app.
