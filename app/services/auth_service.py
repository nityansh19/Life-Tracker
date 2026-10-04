from __future__ import annotations

import asyncio
from dataclasses import dataclass

import flet_secure_storage as fss
from supabase import Client, create_client

from app.config import SUPABASE_PUBLISHABLE_KEY, SUPABASE_URL


@dataclass(slots=True)
class AuthResult:
    ok: bool
    message: str = ""
    needs_email_confirmation: bool = False


class AuthService:
    ACCESS_KEY = "arc_access_token"
    REFRESH_KEY = "arc_refresh_token"

    def __init__(self) -> None:
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY)
        self.storage = fss.SecureStorage(
            android_options=fss.AndroidOptions(
                reset_on_error=True,
                migrate_on_algorithm_change=True,
            )
        )
        self.user = None

    @property
    def is_authenticated(self) -> bool:
        return self.user is not None

    @property
    def user_id(self) -> str | None:
        return str(self.user.id) if self.user else None

    @property
    def email(self) -> str:
        return str(getattr(self.user, "email", "") or "") if self.user else ""

    async def restore_session(self) -> bool:
        refresh_token = await self.storage.get(self.REFRESH_KEY)
        if not refresh_token:
            return False
        try:
            response = await asyncio.to_thread(self.client.auth.refresh_session, refresh_token)
            if response.session is None:
                await self.clear_tokens()
                return False
            await self._persist_session(response.session)
            verified = await asyncio.to_thread(self.client.auth.get_user)
            self.user = verified.user
            return self.user is not None
        except Exception:
            await self.clear_tokens()
            self.user = None
            return False

    async def sign_in(self, email: str, password: str) -> AuthResult:
        try:
            response = await asyncio.to_thread(
                self.client.auth.sign_in_with_password,
                {"email": email.strip(), "password": password},
            )
            if response.session is None or response.user is None:
                return AuthResult(False, "Could not create a session.")
            self.user = response.user
            await self._persist_session(response.session)
            await asyncio.to_thread(self.ensure_profile)
            return AuthResult(True)
        except Exception as exc:
            return AuthResult(False, self._friendly_error(exc))

    async def sign_up(self, name: str, email: str, password: str) -> AuthResult:
        clean_name = name.strip()
        if not clean_name:
            return AuthResult(False, "Enter your name.")
        if len(password) < 8:
            return AuthResult(False, "Use at least 8 characters for your password.")
        try:
            response = await asyncio.to_thread(
                self.client.auth.sign_up,
                {
                    "email": email.strip(),
                    "password": password,
                    "options": {"data": {"display_name": clean_name}},
                },
            )
            if response.session is None:
                return AuthResult(
                    True,
                    "Account created. Check your email to confirm it, then sign in.",
                    needs_email_confirmation=True,
                )
            self.user = response.user
            await self._persist_session(response.session)
            await asyncio.to_thread(self.ensure_profile, clean_name)
            return AuthResult(True)
        except Exception as exc:
            return AuthResult(False, self._friendly_error(exc))

    def ensure_profile(self, display_name: str | None = None) -> dict:
        """Return the user's ARC profile, creating it once when missing.

        Do not use UPSERT here. ARC intentionally grants authenticated users
        UPDATE access only to editable profile columns, while the server-owned
        plan column remains read-only. Postgres UPSERT requires UPDATE
        privileges for its conflict path, even when the row may only need an
        INSERT.
        """
        if not self.user:
            return {}

        existing = self.get_profile()
        if existing:
            return existing

        metadata = getattr(self.user, "user_metadata", None) or {}
        name = (
            display_name
            or metadata.get("display_name")
            or self.email.split("@")[0]
            or "ARC User"
        ).strip()

        self.client.table("arc_profiles").insert(
            {
                "user_id": self.user_id,
                "display_name": name[:40],
                "plan": "free",
            }
        ).execute()
        return self.get_profile()

    def get_profile(self) -> dict:
        if not self.user:
            return {}
        result = (
            self.client.table("arc_profiles")
            .select("user_id,display_name,plan,created_at,updated_at")
            .eq("user_id", self.user_id)
            .maybe_single()
            .execute()
        )
        return result.data or {}

    async def sign_out(self) -> None:
        try:
            await asyncio.to_thread(self.client.auth.sign_out)
        finally:
            self.user = None
            await self.clear_tokens()

    async def clear_tokens(self) -> None:
        await self.storage.remove(self.ACCESS_KEY)
        await self.storage.remove(self.REFRESH_KEY)

    async def _persist_session(self, session) -> None:
        await self.storage.set(self.ACCESS_KEY, session.access_token)
        await self.storage.set(self.REFRESH_KEY, session.refresh_token)

    @staticmethod
    def _friendly_error(exc: Exception) -> str:
        text = str(exc).lower()
        if "invalid login" in text or "invalid credentials" in text:
            return "Email or password is incorrect."
        if "email not confirmed" in text:
            return "Confirm your email first, then sign in."
        if "already registered" in text:
            return "An account with this email already exists."
        if "network" in text or "connect" in text or "timeout" in text:
            return "ARC cannot reach the cloud right now. Check your internet connection."
        if "permission denied" in text or "42501" in text:
            return "ARC couldn't finish account setup. Update ARC and try again."
        return "ARC couldn't finish signing you in. Please try again."
