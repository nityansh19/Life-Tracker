from __future__ import annotations

from datetime import datetime, timezone

from app.config import CLOUD_SCHEMA_VERSION
from app.services.auth_service import AuthService
from app.services.database import Database
from app.services.settings_service import SettingsService


class CloudSyncService:
    def __init__(self, database: Database, auth: AuthService) -> None:
        self.database = database
        self.auth = auth

    def restore_or_seed(self) -> str:
        user_id = self.auth.user_id
        if not user_id:
            raise RuntimeError("Cloud sync requires an authenticated user")

        settings = SettingsService(self.database)
        owner_id = settings.get("cloud_owner_id")
        onboarding_complete = settings.get_bool("onboarding_complete")
        remote = (
            self.auth.client.table("arc_user_state")
            .select("state,schema_version,updated_at")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        ).data

        if remote and remote.get("state"):
            self.database.import_state(remote["state"])
            SettingsService(self.database).set("cloud_owner_id", user_id)
            return "restored"

        if owner_id and owner_id != user_id:
            self.database.reset_user_state()
            onboarding_complete = False

        if not onboarding_complete:
            profile = self.auth.get_profile()
            display_name = (profile.get("display_name") or "ARC User").strip()
            with self.database.connection() as connection:
                connection.execute(
                    "UPDATE users SET name = ? WHERE id = (SELECT id FROM users ORDER BY id LIMIT 1)",
                    (display_name[:40],),
                )

        SettingsService(self.database).set("cloud_owner_id", user_id)
        self.push_local()
        return "seeded"

    def push_local(self) -> None:
        user_id = self.auth.user_id
        if not user_id:
            return
        payload = {
            "user_id": user_id,
            "state": self.database.export_state(),
            "schema_version": CLOUD_SCHEMA_VERSION,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.auth.client.table("arc_user_state").upsert(payload, on_conflict="user_id").execute()

        with self.database.connection() as connection:
            row = connection.execute("SELECT name FROM users ORDER BY id LIMIT 1").fetchone()
        if row:
            self.auth.client.table("arc_profiles").update(
                {
                    "display_name": row["name"][:40],
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            ).eq("user_id", user_id).execute()
