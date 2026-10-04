from __future__ import annotations

from datetime import date, timedelta

import flet as ft

from app.services.database import Database
from app.utils.constants import APP_BG, BORDER, CARD_BG, DANGER, SUCCESS, TEXT_MUTED, TEXT_PRIMARY


def build_calendar_screen(database: Database) -> ft.Control:
    with database.connection() as connection:
        rows = connection.execute(
            "SELECT date, completed, completion_percentage FROM daily_completion ORDER BY date DESC LIMIT 30"
        ).fetchall()
    records = {row["date"]: row for row in rows}

    day_cards = []
    for offset in range(14):
        current = date.today() - timedelta(days=offset)
        record = records.get(current.isoformat())
        completed = bool(record["completed"]) if record else False
        percentage = float(record["completion_percentage"]) if record else 0.0
        color = SUCCESS if completed else TEXT_MUTED if current == date.today() else DANGER
        label = "Perfect" if completed else "In progress" if current == date.today() else "No perfect day"
        day_cards.append(
            ft.Container(
                bgcolor=CARD_BG,
                border=ft.Border.all(1, BORDER),
                border_radius=18,
                padding=15,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text(current.strftime("%A"), size=14, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                                ft.Text(current.strftime("%d %B %Y"), size=11, color=TEXT_MUTED),
                            ],
                        ),
                        ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.END,
                            spacing=2,
                            controls=[
                                ft.Text(label, size=12, color=color, weight=ft.FontWeight.BOLD),
                                ft.Text(f"{round(percentage)}%", size=11, color=TEXT_MUTED),
                            ],
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
            spacing=14,
            controls=[
                ft.Text("History", size=28, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text("Your recent days at a glance.", size=14, color=TEXT_MUTED),
                *day_cards,
            ],
        ),
    )
