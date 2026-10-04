from __future__ import annotations

from datetime import datetime

import flet as ft

from app.components.habit_card import habit_card
from app.components.progress_ring import progress_ring
from app.components.streak_card import streak_card
from app.services.database import Database
from app.services.day_service import DayService
from app.services.habit_service import HabitService
from app.services.streak_service import StreakService
from app.services.user_service import UserService
from app.services.xp_service import XpService
from app.utils.constants import ACCENT, APP_BG, CARD_BG_ALT, MOTIVATION, TEXT_MUTED, TEXT_PRIMARY


def _greeting() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    if hour < 18:
        return "Good afternoon"
    return "Good evening"


def _format_value(item: dict) -> str:
    if item["goal_type"] == "boolean":
        return "Completed" if item["completed"] else "Not completed"
    value = float(item["value"])
    unit = item["unit"]
    if unit == "ml":
        return f"{value / 1000:.1f}L"
    if unit == "minutes":
        hours, minutes = divmod(int(value), 60)
        return f"{hours}h {minutes}m" if hours else f"{minutes}m"
    if unit == "steps":
        return f"{int(value):,} steps"
    return f"{value:g} {unit}".strip()


def build_home_screen(
    page: ft.Page,
    database: Database,
    habits: HabitService,
    streaks: StreakService,
    days: DayService,
    on_refresh,
    on_manage_habits,
) -> ft.Control:
    snapshot = habits.dashboard_snapshot()
    streak = streaks.snapshot()
    user = UserService(database).get()
    xp = XpService(database).snapshot()
    journey_day = days.journey_day_number()

    def show_completion() -> None:
        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("🔥 PERFECT DAY", text_align=ft.TextAlign.CENTER),
                content=ft.Column(
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                    controls=[
                        ft.Icon(ft.Icons.LOCAL_FIRE_DEPARTMENT, size=62, color="#FF9A4A"),
                        ft.Text("Another day conquered.", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text("+100 XP · your streak has been recalculated", color=TEXT_MUTED),
                    ],
                ),
                actions=[ft.FilledButton(content="Keep going", on_click=lambda e: page.pop_dialog())],
                actions_alignment=ft.MainAxisAlignment.CENTER,
            )
        )

    def handle_result(result: dict) -> None:
        on_refresh()
        if result.get("newly_completed"):
            show_completion()

    def toggle(habit_id: int) -> None:
        handle_result(habits.toggle_boolean(habit_id))

    def increment(habit_id: int, amount: float) -> None:
        handle_result(habits.increment(habit_id, amount))

    def show_summary(e=None) -> None:
        detail = days.day_detail(datetime.now().date())
        rows = [
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(item["name"], color=TEXT_PRIMARY),
                    ft.Text(
                        _format_value(item),
                        color="#62D99A" if item["completed"] else TEXT_MUTED,
                    ),
                ],
            )
            for item in detail["habits"]
        ]
        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                scrollable=True,
                title=ft.Text("Today's summary"),
                content=ft.Column(
                    width=380,
                    tight=True,
                    spacing=10,
                    controls=[
                        *rows,
                        ft.Divider(),
                        ft.Text(
                            f"Required progress: {detail['completed_required']} / {detail['scheduled_required']} · {round(detail['percentage'])}%",
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                ),
                actions=[ft.TextButton(content="Close", on_click=lambda e: page.pop_dialog())],
            )
        )

    cards = [
        habit_card(habit, snapshot["progress"].get(habit.id, {}), toggle, increment)
        for habit in snapshot["habits"]
    ]
    motivation = MOTIVATION[min(int(snapshot["percentage"] // 25), len(MOTIVATION) - 1)]

    return ft.Container(
        expand=True,
        bgcolor=APP_BG,
        padding=ft.Padding(left=18, right=18, top=24, bottom=30),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=18,
            controls=[
                ft.Column(
                    spacing=3,
                    controls=[
                        ft.Text(f"{_greeting()}, {user['name']}", size=28, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ft.Text(f"Day {journey_day} of your journey · {xp['title']}", size=14, color=TEXT_MUTED),
                    ],
                ),
                ft.Container(
                    bgcolor=CARD_BG_ALT,
                    border_radius=28,
                    padding=22,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12,
                        controls=[
                            ft.Text("TODAY'S MISSION", size=11, color=TEXT_MUTED, weight=ft.FontWeight.BOLD),
                            progress_ring(snapshot["required_completed"], snapshot["required_total"], snapshot["percentage"]),
                            ft.Text(
                                "Another day conquered." if snapshot["day_completed"] else motivation,
                                size=13,
                                color=TEXT_MUTED,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.ProgressBar(value=float(xp["level_progress"]), color=ACCENT, bgcolor="#24242D", height=6),
                            ft.Text(f"Level {xp['level']} · {xp['xp']} XP", size=11, color=TEXT_MUTED),
                        ],
                    ),
                ),
                streak_card(int(streak["current_streak"]), int(streak["longest_streak"])),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text("Daily goals", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                                ft.Text(
                                    f"{snapshot['required_completed']} / {snapshot['required_total']} required today",
                                    size=12,
                                    color=TEXT_MUTED,
                                ),
                            ],
                        ),
                        ft.FilledTonalButton(content="Manage", icon=ft.Icons.TUNE, on_click=lambda e: on_manage_habits()),
                    ],
                ),
                *cards,
                ft.Row(
                    controls=[
                        ft.OutlinedButton(content="Today summary", icon=ft.Icons.SUMMARIZE_OUTLINED, on_click=show_summary),
                        ft.OutlinedButton(content="Add habit", icon=ft.Icons.ADD, on_click=lambda e: on_manage_habits()),
                    ]
                ),
            ],
        ),
    )
