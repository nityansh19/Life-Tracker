from __future__ import annotations

import calendar as pycalendar
from datetime import date

import flet as ft

from app.services.database import Database
from app.services.day_service import DayService
from app.utils.constants import ACCENT, APP_BG, BORDER, CARD_BG, DANGER, SUCCESS, TEXT_MUTED, TEXT_PRIMARY


def build_calendar_screen(page: ft.Page, database: Database, days: DayService) -> ft.Control:
    days.sync_history()
    today = date.today()
    year, month = today.year, today.month
    first_weekday, total_days = pycalendar.monthrange(year, month)

    with database.connection() as connection:
        rows = connection.execute(
            "SELECT date, completed, completion_percentage FROM daily_completion WHERE date LIKE ?",
            (f"{year:04d}-{month:02d}-%",),
        ).fetchall()
    records = {row["date"]: row for row in rows}

    def show_day(target: date) -> None:
        if target > today:
            return
        detail = days.day_detail(target)
        habit_rows = []
        for item in detail["habits"]:
            value = "Done" if item["goal_type"] == "boolean" and item["completed"] else "Missed" if item["goal_type"] == "boolean" else f"{item['value']:g} {item['unit']}"
            habit_rows.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(item["name"], color=TEXT_PRIMARY),
                        ft.Text(value, color=SUCCESS if item["completed"] else TEXT_MUTED),
                    ],
                )
            )
        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                scrollable=True,
                title=ft.Text(target.strftime("%A, %d %B")),
                content=ft.Column(
                    width=380,
                    tight=True,
                    spacing=10,
                    controls=[
                        ft.Text(
                            "Perfect day" if detail["completed"] else f"{round(detail['percentage'])}% complete",
                            weight=ft.FontWeight.BOLD,
                            color=SUCCESS if detail["completed"] else TEXT_PRIMARY,
                        ),
                        *habit_rows,
                    ],
                ),
                actions=[ft.TextButton(content="Close", on_click=lambda e: page.pop_dialog())],
            )
        )

    cells: list[ft.Control] = [ft.Container(height=48) for _ in range(first_weekday)]
    for day_number in range(1, total_days + 1):
        target = date(year, month, day_number)
        row = records.get(target.isoformat())
        is_today = target == today
        is_future = target > today
        completed = bool(row["completed"]) if row else False
        percentage = float(row["completion_percentage"]) if row else 0.0

        if is_future:
            bgcolor = "#101014"
            number_color = "#4E4E58"
        elif completed:
            bgcolor = "#153326"
            number_color = SUCCESS
        elif row:
            bgcolor = "#2A181B"
            number_color = DANGER
        else:
            bgcolor = CARD_BG
            number_color = TEXT_MUTED

        cells.append(
            ft.Container(
                height=52,
                border_radius=14,
                bgcolor=bgcolor,
                border=ft.Border.all(1, ACCENT if is_today else BORDER),
                alignment=ft.Alignment.CENTER,
                on_click=(lambda e, d=target: show_day(d)) if not is_future else None,
                content=ft.Column(
                    tight=True,
                    spacing=1,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Text(str(day_number), size=13, weight=ft.FontWeight.BOLD, color=number_color),
                        ft.Text("✓" if completed else f"{round(percentage)}%" if row else "", size=9, color=number_color),
                    ],
                ),
            )
        )

    while len(cells) % 7:
        cells.append(ft.Container(height=48))

    week_rows = [
        ft.Row(
            controls=[ft.Container(expand=True, content=cell) for cell in cells[i : i + 7]],
            spacing=6,
        )
        for i in range(0, len(cells), 7)
    ]

    recent = days.recent_days(21)
    recent_cards = []
    for row in recent:
        target = date.fromisoformat(row["date"])
        recent_cards.append(
            ft.Container(
                bgcolor=CARD_BG,
                border=ft.Border.all(1, BORDER),
                border_radius=16,
                padding=14,
                on_click=lambda e, d=target: show_day(d),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text(target.strftime("%A"), weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                                ft.Text(target.strftime("%d %b %Y"), size=11, color=TEXT_MUTED),
                            ],
                        ),
                        ft.Text(
                            "Perfect" if bool(row["completed"]) else f"{round(float(row['completion_percentage']))}%",
                            color=SUCCESS if bool(row["completed"]) else TEXT_MUTED,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                ),
            )
        )

    return ft.Container(
        expand=True,
        bgcolor=APP_BG,
        padding=ft.Padding(left=18, right=18, top=24, bottom=30),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                ft.Text("Calendar", size=28, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text("Tap any past day to inspect exactly what happened.", color=TEXT_MUTED),
                ft.Container(
                    bgcolor=CARD_BG,
                    border=ft.Border.all(1, BORDER),
                    border_radius=24,
                    padding=16,
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Text(today.strftime("%B %Y"), size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                            ft.Row(
                                controls=[
                                    ft.Container(expand=True, content=ft.Text(label, size=10, color=TEXT_MUTED, text_align=ft.TextAlign.CENTER))
                                    for label in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
                                ]
                            ),
                            *week_rows,
                        ],
                    ),
                ),
                ft.Text("Recent history", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                *recent_cards,
            ],
        ),
    )
