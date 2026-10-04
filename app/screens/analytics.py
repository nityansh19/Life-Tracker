import flet as ft

from app.services.analytics_service import AnalyticsService
from app.services.database import Database
from app.services.streak_service import StreakService
from app.utils.constants import ACCENT, APP_BG, BORDER, CARD_BG, TEXT_MUTED, TEXT_PRIMARY


def _metric(label: str, value: str, subtitle: str = "") -> ft.Control:
    return ft.Container(
        expand=True,
        bgcolor=CARD_BG,
        border=ft.Border.all(1, BORDER),
        border_radius=20,
        padding=17,
        content=ft.Column(
            spacing=4,
            controls=[
                ft.Text(label.upper(), size=10, color=TEXT_MUTED, weight=ft.FontWeight.BOLD),
                ft.Text(value, size=25, color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
                ft.Text(subtitle, size=11, color=TEXT_MUTED) if subtitle else ft.Container(height=0),
            ],
        ),
    )


def build_analytics_screen(database: Database, streaks: StreakService) -> ft.Control:
    analytics = AnalyticsService(database)
    weekly = analytics.completion_rate(7)
    monthly = analytics.completion_rate(30)
    totals = analytics.totals()
    streak = streaks.snapshot()

    return ft.Container(
        expand=True,
        bgcolor=APP_BG,
        padding=ft.Padding(left=18, right=18, top=24, bottom=30),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                ft.Text("Progress", size=28, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text("Consistency, not noise.", size=14, color=TEXT_MUTED),
                ft.Container(
                    bgcolor=CARD_BG,
                    border_radius=24,
                    border=ft.Border.all(1, BORDER),
                    padding=20,
                    content=ft.Column(
                        spacing=12,
                        controls=[
                            ft.Text("WEEKLY COMPLETION", size=11, color=TEXT_MUTED, weight=ft.FontWeight.BOLD),
                            ft.Text(f"{weekly}%", size=38, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                            ft.ProgressBar(
                                value=weekly / 100,
                                color=ACCENT,
                                bgcolor="#24242D",
                                height=9,
                                border_radius=9,
                            ),
                            ft.Text(f"30-day average: {monthly}%", size=12, color=TEXT_MUTED),
                        ],
                    ),
                ),
                ft.Row(
                    controls=[
                        _metric("Current streak", f"{streak['current_streak']}d"),
                        _metric("Best streak", f"{streak['longest_streak']}d"),
                    ]
                ),
                ft.Row(
                    controls=[
                        _metric("Perfect days", str(totals["perfect_days"])),
                        _metric("Habits done", str(totals["completed_habits"])),
                    ]
                ),
            ],
        ),
    )
