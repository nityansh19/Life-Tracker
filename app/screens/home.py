from __future__ import annotations

from datetime import datetime

import flet as ft

from app.components.habit_card import habit_card
from app.components.progress_ring import progress_ring
from app.components.streak_card import streak_card
from app.services.habit_service import HabitService
from app.services.streak_service import StreakService
from app.utils.constants import APP_BG, CARD_BG_ALT, TEXT_MUTED, TEXT_PRIMARY


def _greeting() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    if hour < 18:
        return "Good afternoon"
    return "Good evening"


def build_home_screen(habits: HabitService, streaks: StreakService, on_refresh) -> ft.Control:
    snapshot = habits.dashboard_snapshot()
    streak = streaks.snapshot()

    def toggle(habit_id: int) -> None:
        habits.toggle_boolean(habit_id)
        on_refresh()

    def increment(habit_id: int, amount: float) -> None:
        habits.increment(habit_id, amount)
        on_refresh()

    cards = [
        habit_card(habit, snapshot["progress"].get(habit.id, {}), toggle, increment)
        for habit in snapshot["habits"]
    ]

    status_text = (
        "Another day conquered."
        if snapshot["day_completed"]
        else "Finish every required goal to lock in today."
    )

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
                        ft.Text(f"{_greeting()}, Nityansh", size=28, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ft.Text("Build your arc one perfect day at a time.", size=14, color=TEXT_MUTED),
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
                            progress_ring(
                                snapshot["required_completed"],
                                snapshot["required_total"],
                                snapshot["percentage"],
                            ),
                            ft.Text(status_text, size=13, color=TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                        ],
                    ),
                ),
                streak_card(int(streak["current_streak"]), int(streak["longest_streak"])),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Daily goals", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ft.Text(
                            f"{snapshot['required_completed']} / {snapshot['required_total']} required",
                            size=12,
                            color=TEXT_MUTED,
                        ),
                    ],
                ),
                *cards,
            ],
        ),
    )
