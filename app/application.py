from __future__ import annotations

import flet as ft

from app.components.navigation import build_navigation
from app.screens.achievements import build_achievements_screen
from app.screens.analytics import build_analytics_screen
from app.screens.calendar import build_calendar_screen
from app.screens.habits import build_habits_screen
from app.screens.home import build_home_screen
from app.screens.onboarding import build_onboarding_screen
from app.screens.profile import build_profile_screen
from app.services.achievement_service import AchievementService
from app.services.database import Database
from app.services.day_service import DayService
from app.services.habit_service import HabitService
from app.services.settings_service import SettingsService
from app.services.streak_service import StreakService
from app.utils.constants import ACCENT, APP_BG


class ArcApplication:
    """Root controller for navigation, first launch, and service wiring."""

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.database = Database()
        self.database.initialize()
        self.settings = SettingsService(self.database)
        self.habits = HabitService(self.database)
        self.streaks = StreakService(self.database)
        self.days = DayService(self.database)
        self.achievements = AchievementService(self.database)
        self.selected_index = 0
        self.subview: str | None = None

        self._configure_page()
        if self.settings.get_bool("onboarding_complete"):
            self.days.sync_history()
            self.achievements.sync()
        self.render()

    def _configure_page(self) -> None:
        self.page.title = "ARC — Daily Life Tracker"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = APP_BG
        self.page.padding = 0
        self.page.spacing = 0
        self.page.theme = ft.Theme(color_scheme_seed=ACCENT, use_material3=True)

    def render(self) -> None:
        self.page.controls.clear()

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
                    on_refresh=self.render,
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
                on_refresh=self.render,
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
                on_refresh=self.render,
            ),
        ]

        self.page.add(screens[self.selected_index]())
        self.page.navigation_bar = build_navigation(
            selected_index=self.selected_index,
            on_change=self._on_navigation_change,
        )
        self.page.update()

    def _finish_onboarding(self) -> None:
        self.days.sync_history()
        self.achievements.sync()
        self.render()

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
