from __future__ import annotations

import asyncio

import flet as ft

from app.components.navigation import build_navigation
from app.screens.achievements import build_achievements_screen
from app.screens.analytics import build_analytics_screen
from app.screens.auth import build_auth_screen
from app.screens.calendar import build_calendar_screen
from app.screens.habits import build_habits_screen
from app.screens.home import build_home_screen
from app.screens.onboarding import build_onboarding_screen
from app.screens.preview import build_preview_screen
from app.screens.profile import build_profile_screen
from app.services.achievement_service import AchievementService
from app.services.auth_service import AuthResult, AuthService
from app.services.cloud_sync_service import CloudSyncService
from app.services.database import Database
from app.services.day_service import DayService
from app.services.habit_service import HabitService
from app.services.settings_service import SettingsService
from app.services.streak_service import StreakService
from app.utils.constants import ACCENT, APP_BG


class ArcApplication:
    """Launch controller: preview -> auth -> onboarding -> private tracker."""

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.database = Database()
        self.database.initialize()

        self.auth = AuthService()
        self.cloud = CloudSyncService(self.database, self.auth)
        self.settings = SettingsService(self.database)
        self.habits = HabitService(self.database)
        self.streaks = StreakService(self.database)
        self.days = DayService(self.database)
        self.achievements = AchievementService(self.database)

        self.selected_index = 0
        self.subview: str | None = None
        self.public_view = "preview"
        self.auth_mode = "signup"
        self.cloud_status = "Not signed in"
        self.account_profile: dict = {}
        self._sync_lock = asyncio.Lock()

        self._configure_page()

    async def initialize(self) -> None:
        restored = await self.auth.restore_session()
        if restored:
            try:
                self.account_profile = await asyncio.to_thread(self.auth.ensure_profile)
                result = await asyncio.to_thread(self.cloud.restore_or_seed)
                self.cloud_status = "Cloud restored" if result == "restored" else "Cloud connected"
                self._after_state_change()
            except Exception:
                self.cloud_status = "Offline mode"
        self.render()

    def _configure_page(self) -> None:
        self.page.title = "ARC — Daily Life Tracker"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = APP_BG
        self.page.padding = 0
        self.page.spacing = 0
        self.page.theme = ft.Theme(color_scheme_seed=ACCENT, use_material3=True)

    def _after_state_change(self) -> None:
        self.settings = SettingsService(self.database)
        self.habits = HabitService(self.database)
        self.streaks = StreakService(self.database)
        self.days = DayService(self.database)
        self.achievements = AchievementService(self.database)
        if self.settings.get_bool("onboarding_complete"):
            self.days.sync_history()
            self.achievements.sync()

    def render(self) -> None:
        self.page.controls.clear()

        if not self.auth.is_authenticated:
            self.page.navigation_bar = None
            if self.public_view == "auth":
                self.page.add(
                    build_auth_screen(
                        page=self.page,
                        mode=self.auth_mode,
                        on_back=self._show_preview,
                        on_switch=self._switch_auth_mode,
                        on_login=self._login,
                        on_signup=self._signup,
                    )
                )
            else:
                self.page.add(
                    build_preview_screen(
                        on_start=lambda: self._show_auth("signup"),
                        on_sign_in=lambda: self._show_auth("login"),
                    )
                )
            self.page.update()
            return

        if not self.settings.get_bool("onboarding_complete"):
            self.page.navigation_bar = None
            self.page.add(
                build_onboarding_screen(
                    page=self.page,
                    database=self.database,
                    settings=self.settings,
                    on_finish=self._finish_onboarding,
                )
            )
            self.page.update()
            return

        if self.subview == "habits":
            self.page.navigation_bar = None
            self.page.add(
                build_habits_screen(
                    page=self.page,
                    habits=self.habits,
                    on_back=self._close_subview,
                    on_refresh=self.refresh_and_sync,
                )
            )
            self.page.update()
            return

        screens = [
            lambda: build_home_screen(
                page=self.page,
                database=self.database,
                habits=self.habits,
                streaks=self.streaks,
                days=self.days,
                on_refresh=self.refresh_and_sync,
                on_manage_habits=self._open_habits,
            ),
            lambda: build_calendar_screen(self.page, self.database, self.days),
            lambda: build_analytics_screen(self.database, self.streaks),
            lambda: build_achievements_screen(self.database),
            lambda: build_profile_screen(
                page=self.page,
                database=self.database,
                streaks=self.streaks,
                on_manage_habits=self._open_habits,
                on_refresh=self.refresh_and_sync,
                account_email=self.auth.email,
                plan=str(self.account_profile.get("plan") or "free"),
                cloud_status=self.cloud_status,
                on_sync=self._manual_sync,
                on_logout=self._logout,
            ),
        ]

        self.page.add(screens[self.selected_index]())
        self.page.navigation_bar = build_navigation(
            selected_index=self.selected_index,
            on_change=self._on_navigation_change,
        )
        self.page.update()

    def refresh_and_sync(self) -> None:
        self.render()
        if self.auth.is_authenticated and self.settings.get_bool("onboarding_complete"):
            self.cloud_status = "Syncing..."
            self.page.run_task(self._background_sync)

    async def _background_sync(self) -> None:
        async with self._sync_lock:
            try:
                await asyncio.to_thread(self.cloud.push_local)
                self.cloud_status = "Synced"
            except Exception:
                self.cloud_status = "Offline changes saved locally"

    async def _manual_sync(self, e=None) -> None:
        self.cloud_status = "Syncing..."
        self.render()
        await self._background_sync()
        try:
            self.account_profile = await asyncio.to_thread(self.auth.get_profile)
        except Exception:
            pass
        self.render()

    async def _login(self, email: str, password: str) -> AuthResult:
        result = await self.auth.sign_in(email, password)
        if not result.ok:
            return result
        try:
            self.account_profile = await asyncio.to_thread(self.auth.get_profile)
            state = await asyncio.to_thread(self.cloud.restore_or_seed)
            self.cloud_status = "Cloud restored" if state == "restored" else "Cloud connected"
            self._after_state_change()
            self.public_view = "preview"
            self.render()
            return result
        except Exception as exc:
            await self.auth.sign_out()
            self.account_profile = {}
            return AuthResult(False, f"Signed in, but cloud setup failed: {str(exc)[:120]}")

    async def _signup(self, name: str, email: str, password: str) -> AuthResult:
        result = await self.auth.sign_up(name, email, password)
        if not result.ok or result.needs_email_confirmation:
            return result
        try:
            self.account_profile = await asyncio.to_thread(self.auth.get_profile)
            await asyncio.to_thread(self.cloud.restore_or_seed)
            self.cloud_status = "Cloud connected"
            self._after_state_change()
            self.render()
            return result
        except Exception as exc:
            await self.auth.sign_out()
            self.account_profile = {}
            return AuthResult(False, f"Account created, but cloud setup failed: {str(exc)[:120]}")

    async def _logout(self, e=None) -> None:
        try:
            if self.settings.get_bool("onboarding_complete"):
                await asyncio.to_thread(self.cloud.push_local)
        except Exception:
            pass
        await self.auth.sign_out()
        self.account_profile = {}
        self.public_view = "preview"
        self.selected_index = 0
        self.subview = None
        self.cloud_status = "Not signed in"
        self.render()

    def _show_preview(self) -> None:
        self.public_view = "preview"
        self.render()

    def _show_auth(self, mode: str) -> None:
        self.public_view = "auth"
        self.auth_mode = mode
        self.render()

    def _switch_auth_mode(self, mode: str) -> None:
        self.auth_mode = mode
        self.render()

    def _finish_onboarding(self) -> None:
        self.days.sync_history()
        self.achievements.sync()
        self.refresh_and_sync()

    def _open_habits(self) -> None:
        self.subview = "habits"
        self.render()

    def _close_subview(self) -> None:
        self.subview = None
        self.render()

    def _on_navigation_change(self, event: ft.Event[ft.NavigationBar]) -> None:
        self.selected_index = int(event.control.selected_index or 0)
        self.subview = None
        self.render()
