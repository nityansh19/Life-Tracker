from __future__ import annotations

import flet as ft

from app.models.habit import Habit
from app.services.habit_service import HabitService
from app.utils.constants import (
    ACCENT,
    APP_BG,
    BORDER,
    CARD_BG,
    DANGER,
    HABIT_CATEGORIES,
    SUCCESS,
    TEXT_MUTED,
    TEXT_PRIMARY,
    WEEKDAY_CODES,
    WEEKDAY_LABELS,
)


def build_habits_screen(
    page: ft.Page,
    habits: HabitService,
    on_back,
    on_refresh,
) -> ft.Control:
    active_habits = habits.get_all_habits(active_only=True)
    archived_habits = habits.get_all_habits(active_only=False)

    def open_editor(habit: Habit | None = None) -> None:
        editing = habit is not None

        name_field = ft.TextField(
            label="Habit name",
            value=habit.name if habit else "",
            max_length=60,
            autofocus=True,
        )
        category_field = ft.Dropdown(
            label="Category",
            value=habit.category if habit else "Custom",
            options=[
                ft.DropdownOption(key=category, text=category)
                for category in HABIT_CATEGORIES
            ],
        )
        goal_type_field = ft.Dropdown(
            label="Goal type",
            value=habit.goal_type if habit else "boolean",
            options=[
                ft.DropdownOption(key="boolean", text="Done / not done"),
                ft.DropdownOption(key="number", text="Number target"),
            ],
        )
        goal_amount_field = ft.TextField(
            label="Target amount",
            value=(
                str(int(habit.goal_amount))
                if habit and habit.goal_amount.is_integer()
                else str(habit.goal_amount)
                if habit
                else "1"
            ),
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        unit_field = ft.TextField(
            label="Unit",
            hint_text="steps, ml, minutes, pages...",
            value=habit.unit if habit and habit.goal_type == "number" else "",
        )
        required_switch = ft.Switch(
            label="Required for a perfect day",
            value=habit.required if habit else True,
        )
        error_text = ft.Text("", color=DANGER, size=12)

        selected_schedule = (
            set(WEEKDAY_CODES)
            if not habit or habit.schedule == "daily"
            else {part for part in habit.schedule.split(",") if part}
        )
        day_checks = [
            ft.Checkbox(label=label, value=code in selected_schedule)
            for code, label in zip(WEEKDAY_CODES, WEEKDAY_LABELS)
        ]

        def collect_schedule() -> str:
            selected = [
                code
                for code, checkbox in zip(WEEKDAY_CODES, day_checks)
                if checkbox.value
            ]
            if len(selected) == 7:
                return "daily"
            return ",".join(selected)

        def save_habit(e=None) -> None:
            try:
                goal_type = str(goal_type_field.value or "boolean")
                amount = 1.0 if goal_type == "boolean" else float(goal_amount_field.value or 0)
                payload = dict(
                    name=name_field.value or "",
                    category=str(category_field.value or "Custom"),
                    goal_type=goal_type,
                    goal_amount=amount,
                    unit=unit_field.value or "",
                    required=bool(required_switch.value),
                    schedule=collect_schedule(),
                )
                if editing and habit is not None:
                    habits.update_habit(habit.id, **payload)
                else:
                    habits.create_habit(**payload)
            except (TypeError, ValueError) as exc:
                error_text.value = str(exc)
                error_text.update()
                return

            page.pop_dialog()
            on_refresh()

        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                scrollable=True,
                title=ft.Text("Edit habit" if editing else "Create habit"),
                content=ft.Column(
                    width=380,
                    tight=True,
                    spacing=12,
                    controls=[
                        name_field,
                        category_field,
                        goal_type_field,
                        ft.Row(
                            controls=[
                                ft.Container(expand=True, content=goal_amount_field),
                                ft.Container(expand=True, content=unit_field),
                            ]
                        ),
                        required_switch,
                        ft.Text(
                            "Repeat on",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=TEXT_MUTED,
                        ),
                        ft.Row(controls=day_checks[:4]),
                        ft.Row(controls=day_checks[4:]),
                        ft.Text(
                            "For done/not-done habits, target amount is automatically 1.",
                            size=11,
                            color=TEXT_MUTED,
                        ),
                        error_text,
                    ],
                ),
                actions=[
                    ft.TextButton(content="Cancel", on_click=lambda e: page.pop_dialog()),
                    ft.FilledButton(content="Save habit", on_click=save_habit),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    def confirm_archive(habit: Habit) -> None:
        def archive(e=None) -> None:
            habits.archive_habit(habit.id)
            page.pop_dialog()
            on_refresh()

        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Archive habit?"),
                content=ft.Text(
                    f'"{habit.name}" will disappear from daily tracking, but its history will be preserved.'
                ),
                actions=[
                    ft.TextButton(content="Cancel", on_click=lambda e: page.pop_dialog()),
                    ft.FilledButton(content="Archive", on_click=archive),
                ],
            )
        )

    def confirm_delete(habit: Habit) -> None:
        def delete_forever(e=None) -> None:
            habits.delete_habit_permanently(habit.id)
            page.pop_dialog()
            on_refresh()

        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Delete permanently?"),
                content=ft.Text(
                    f'This permanently deletes "{habit.name}" and all stored progress for it. This cannot be undone.'
                ),
                actions=[
                    ft.TextButton(content="Cancel", on_click=lambda e: page.pop_dialog()),
                    ft.TextButton(
                        content="Delete forever",
                        on_click=delete_forever,
                        style=ft.ButtonStyle(color=DANGER),
                    ),
                ],
            )
        )

    def active_card(habit: Habit) -> ft.Control:
        goal = (
            "Complete once"
            if habit.goal_type == "boolean"
            else f"{habit.goal_amount:g} {habit.unit}".strip()
        )
        return ft.Container(
            bgcolor=CARD_BG,
            border=ft.Border.all(1, BORDER),
            border_radius=20,
            padding=16,
            content=ft.Column(
                spacing=9,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                expand=True,
                                spacing=2,
                                controls=[
                                    ft.Text(
                                        habit.name,
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        color=TEXT_PRIMARY,
                                    ),
                                    ft.Text(
                                        f"{habit.category} · {goal}",
                                        size=12,
                                        color=TEXT_MUTED,
                                    ),
                                ],
                            ),
                            ft.Text(
                                "REQUIRED" if habit.required else "OPTIONAL",
                                size=10,
                                color=ACCENT if habit.required else TEXT_MUTED,
                                weight=ft.FontWeight.BOLD,
                            ),
                        ],
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                spacing=5,
                                controls=[
                                    ft.Icon(
                                        ft.Icons.CALENDAR_TODAY,
                                        size=15,
                                        color=TEXT_MUTED,
                                    ),
                                    ft.Text(
                                        habit.schedule_label,
                                        size=11,
                                        color=TEXT_MUTED,
                                    ),
                                ],
                            ),
                            ft.Row(
                                spacing=0,
                                controls=[
                                    ft.IconButton(
                                        icon=ft.Icons.EDIT_OUTLINED,
                                        tooltip="Edit",
                                        on_click=lambda e, h=habit: open_editor(h),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.ARCHIVE_OUTLINED,
                                        tooltip="Archive",
                                        on_click=lambda e, h=habit: confirm_archive(h),
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        )

    def archived_card(habit: Habit) -> ft.Control:
        def restore(e=None) -> None:
            habits.restore_habit(habit.id)
            on_refresh()

        return ft.Container(
            bgcolor=CARD_BG,
            border=ft.Border.all(1, BORDER),
            border_radius=18,
            padding=14,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Column(
                        expand=True,
                        spacing=2,
                        controls=[
                            ft.Text(
                                habit.name,
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=TEXT_PRIMARY,
                            ),
                            ft.Text(
                                "Archived · history preserved",
                                size=11,
                                color=TEXT_MUTED,
                            ),
                        ],
                    ),
                    ft.Row(
                        spacing=0,
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.RESTORE,
                                tooltip="Restore",
                                icon_color=SUCCESS,
                                on_click=restore,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_FOREVER_OUTLINED,
                                tooltip="Delete permanently",
                                icon_color=DANGER,
                                on_click=lambda e, h=habit: confirm_delete(h),
                            ),
                        ],
                    ),
                ],
            ),
        )

    active_controls = [active_card(habit) for habit in active_habits]
    archived_controls = [archived_card(habit) for habit in archived_habits]

    controls: list[ft.Control] = [
        ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(
                    spacing=6,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            tooltip="Back",
                            on_click=lambda e: on_back(),
                        ),
                        ft.Column(
                            spacing=1,
                            controls=[
                                ft.Text(
                                    "Habits",
                                    size=27,
                                    weight=ft.FontWeight.BOLD,
                                    color=TEXT_PRIMARY,
                                ),
                                ft.Text(
                                    "Design your daily system.",
                                    size=12,
                                    color=TEXT_MUTED,
                                ),
                            ],
                        ),
                    ],
                ),
                ft.FilledButton(
                    content="Add habit",
                    icon=ft.Icons.ADD,
                    on_click=lambda e: open_editor(),
                ),
            ],
        ),
        ft.Container(
            bgcolor="#151321",
            border_radius=18,
            padding=14,
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.INFO_OUTLINE, color=ACCENT, size=20),
                    ft.Text(
                        "Only required habits scheduled for today decide whether your day is perfect.",
                        expand=True,
                        size=12,
                        color=TEXT_MUTED,
                    ),
                ]
            ),
        ),
        ft.Text(
            f"ACTIVE · {len(active_habits)}",
            size=11,
            color=TEXT_MUTED,
            weight=ft.FontWeight.BOLD,
        ),
        *active_controls,
    ]

    if archived_controls:
        controls.extend(
            [
                ft.Text(
                    f"ARCHIVED · {len(archived_habits)}",
                    size=11,
                    color=TEXT_MUTED,
                    weight=ft.FontWeight.BOLD,
                ),
                *archived_controls,
            ]
        )

    return ft.Container(
        expand=True,
        bgcolor=APP_BG,
        padding=ft.Padding(left=18, right=18, top=20, bottom=30),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=15,
            controls=controls,
        ),
    )
