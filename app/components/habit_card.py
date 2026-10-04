from __future__ import annotations

import flet as ft

from app.models.habit import Habit
from app.utils.constants import ACCENT, BORDER, CARD_BG, SUCCESS, SUCCESS_SOFT, TEXT_MUTED, TEXT_PRIMARY


def _display_value(habit: Habit, value: float) -> str:
    if habit.unit == "ml":
        return f"{value / 1000:.1f}L / {habit.goal_amount / 1000:.1f}L"
    if habit.unit == "minutes":
        hours, minutes = divmod(int(value), 60)
        goal_h, goal_m = divmod(int(habit.goal_amount), 60)
        left = f"{hours}h {minutes:02d}m" if hours else f"{minutes}m"
        right = f"{goal_h}h {goal_m:02d}m" if goal_h else f"{goal_m}m"
        return f"{left} / {right}"
    if habit.unit == "steps":
        return f"{int(value):,} / {int(habit.goal_amount):,}"
    return f"{value:g} / {habit.goal_amount:g} {habit.unit}".strip()


def _quick_increments(habit: Habit) -> list[float]:
    if habit.unit == "steps":
        return [500, 1000]
    if habit.unit == "ml":
        return [250, 500]
    if habit.unit == "minutes":
        return [15, 30]
    small = max(1.0, round(habit.goal_amount * 0.1, 2))
    large = max(small, round(habit.goal_amount * 0.25, 2))
    return [small, large]


def _increment_label(habit: Habit, amount: float) -> str:
    number = f"{amount:g}"
    if habit.unit == "minutes":
        return f"+{number}m"
    if habit.unit == "ml":
        return f"+{number}ml"
    return f"+{number}"


def habit_card(habit: Habit, progress: dict, on_toggle, on_increment) -> ft.Control:
    value = float(progress.get("value", 0))
    completed = bool(progress.get("completed", False))
    status_color = SUCCESS if completed else ACCENT
    progress_value = 1.0 if habit.goal_type == "boolean" and completed else min(value / habit.goal_amount, 1.0)

    if habit.goal_type == "boolean":
        action = ft.FilledButton(
            content="Completed" if completed else "Mark done",
            icon=ft.Icons.CHECK_CIRCLE if completed else ft.Icons.CIRCLE_OUTLINED,
            bgcolor=SUCCESS_SOFT if completed else "#26203E",
            color=SUCCESS if completed else "#BEB1FF",
            on_click=lambda e: on_toggle(habit.id),
        )
    else:
        action = ft.Row(
            spacing=8,
            controls=[
                ft.OutlinedButton(
                    content=_increment_label(habit, amount),
                    on_click=lambda e, a=amount: on_increment(habit.id, a),
                )
                for amount in _quick_increments(habit)
            ],
        )

    return ft.Container(
        bgcolor=CARD_BG,
        border=ft.Border.all(1, BORDER),
        border_radius=22,
        padding=18,
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Row(
                                    spacing=7,
                                    controls=[
                                        ft.Text(habit.name, size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                                        ft.Text("REQUIRED", size=9, color=TEXT_MUTED)
                                        if habit.required
                                        else ft.Text("OPTIONAL", size=9, color=TEXT_MUTED),
                                    ],
                                ),
                                ft.Text(habit.category, size=12, color=TEXT_MUTED),
                            ],
                        ),
                        ft.Icon(
                            ft.Icons.CHECK_CIRCLE if completed else ft.Icons.RADIO_BUTTON_UNCHECKED,
                            color=status_color,
                        ),
                    ],
                ),
                ft.ProgressBar(
                    value=progress_value,
                    color=status_color,
                    bgcolor="#24242D",
                    height=7,
                    border_radius=8,
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(
                            "Done"
                            if habit.goal_type == "boolean" and completed
                            else "Not completed"
                            if habit.goal_type == "boolean"
                            else _display_value(habit, value),
                            size=12,
                            color=TEXT_MUTED,
                        ),
                        action,
                    ],
                ),
            ],
        ),
    )
