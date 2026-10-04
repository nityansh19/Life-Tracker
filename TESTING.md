# ARC 1.0 Release Candidate Testing

## Public launch flow

1. Fresh install must open the public ARC feature preview.
2. Preview users must not be able to reach habit data without signing in.
3. Create an account with email + password.
4. If email confirmation is enabled, verify the email and then sign in.
5. Complete onboarding and confirm the Home screen opens.
6. Log out. ARC should return to the public preview.
7. Sign back in. The same ARC data should restore from Supabase.

## Cloud/offline tests

1. Complete a habit while online and tap Profile -> Sync now.
2. Force-close ARC, reopen, and confirm the secure session restores.
3. Turn off internet and update a habit. ARC must continue working from SQLite.
4. Re-enable internet and tap Sync now. Cloud status should return to Synced.
5. On a second clean device/install, sign into the same account and confirm the cloud snapshot restores.
6. Sign into a different account on the same device. The previous account's local data must not appear.

## Existing beta-user migration

On the first account login after upgrading from 0.9.0, existing local beta data should be adopted by that account if no cloud snapshot already exists.

## Security checks

- Users must only be able to read/write their own arc_profiles and arc_user_state rows.
- The mobile app contains only the Supabase publishable key, never a secret/service-role key.
- The plan field defaults to free and cannot be edited by the mobile client.
- Session tokens are stored through Android secure storage.
- Android app backup is disabled for secure-storage compatibility.
- Before public release, enable Supabase Auth leaked-password protection in the project dashboard.

## Existing tracker regression

Run through:
- custom habit create/edit/archive/restore
- weekday scheduling
- perfect day and XP
- streaks
- calendar day detail
- analytics
- weekly report
- achievements
- profile edits
- restart persistence
