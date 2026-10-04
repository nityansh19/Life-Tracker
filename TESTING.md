# ARC Beta Testing Checklist

This build is intended for the first closed testing round.

## Critical flows

1. Fresh install opens onboarding and saves the selected name, starter habits, and journey date.
2. Mark boolean habits complete, add steps/water/study progress, then force-close and reopen the app. Values must persist.
3. Complete every required habit. The perfect-day dialog should appear once, XP should increase once, and the streak should update.
4. Toggle a completed habit off and on again. Habit XP and perfect-day XP must not be awarded twice.
5. Create a custom numeric habit with selected weekdays. It should only appear on scheduled days.
6. Archive a habit. It should leave today's dashboard while previous stored progress remains available in history.
7. Open Calendar and tap a past day. The app should show completed/missed habits and the saved percentage.
8. Verify Progress shows weekly/monthly completion plus the weekly report.
9. Verify Achievements unlock when their stored criteria are reached.
10. Change the profile name and journey date and reopen the app.

## Date rollover test

For a controlled test, use a separate test database/device. Leave at least one required goal incomplete, close ARC before midnight, then reopen it the next day. The previous day should be stored as incomplete and the new day should start clean.

## Android UI checks

- Small phone width
- Tall phone width
- Scrolling with many habits
- Keyboard open inside Add/Edit Habit
- Bottom navigation remains usable
- Dialogs fit without clipping
- No horizontal overflow on long habit names

## Report bugs with

- Device / Android version
- Exact steps to reproduce
- Screenshot if visual
- Whether the bug survives app restart
