import flet as ft

from app.services.analytics_service import AnalyticsService
from app.services.database import Database
from app.services.streak_service import StreakService
from app.utils.constants import ACCENT, APP_BG, BORDER, CARD_BG, TEXT_MUTED, TEXT_PRIMARY


def build_profile_screen(database: Database, streaks: StreakService) -> ft.Control:
    with database.connection() as connection:
        user = connection.execute("SELECT * FROM users ORDER BY id LIMIT 1").fetchone()
    totals = AnalyticsService(database).totals()
    streak = streaks.snapshot()

    return ft.Container(
        expand=True,
        bgcolor=APP_BG,
        padding=ft.Padding(left=18, right=18, top=24, bottom=30),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                ft.Text("Profile", size=28, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(
                    bgcolor=CARD_BG,
                    border=ft.Border.all(1, BORDER),
                    border_radius=26,
                    padding=22,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                        controls=[
                            ft.CircleAvatar(
                                radius=34,
                                bgcolor="#2B2451",
                                content=ft.Text(
                                    user["name"][0].upper(),
                                    size=26,
                                    weight=ft.FontWeight.BOLD,
                                    color="#D8D0FF",
                                ),
                            ),
                            ft.Text(user["name"], size=22, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                            ft.Text(f"Journey started {user['journey_start_date']}", size=12, color=TEXT_MUTED),
                            ft.ProgressBar(
                                value=min(user["xp"] / 1000, 1),
                                color=ACCENT,
                                bgcolor="#24242D",
                                height=7,
                                border_radius=7,
                            ),
                            ft.Text(f"Level {user['level']} · {user['xp']} XP", size=11, color=TEXT_MUTED),
                        ],
                    ),
                ),
                ft.ListTile(
                    title=ft.Text("Current streak", color=TEXT_PRIMARY),
                    subtitle=ft.Text("Keep it alive", color=TEXT_MUTED),
                    trailing=ft.Text(
                        f"{streak['current_streak']} days",
                        color=TEXT_PRIMARY,
                        weight=ft.FontWeight.BOLD,
                    ),
                ),
                ft.ListTile(
                    title=ft.Text("Best streak", color=TEXT_PRIMARY),
                    trailing=ft.Text(
                        f"{streak['longest_streak']} days",
                        color=TEXT_PRIMARY,
                        weight=ft.FontWeight.BOLD,
                    ),
                ),
                ft.ListTile(
                    title=ft.Text("Perfect days", color=TEXT_PRIMARY),
                    trailing=ft.Text(
                        str(totals["perfect_days"]),
                        color=TEXT_PRIMARY,
                        weight=ft.FontWeight.BOLD,
                    ),
                ),
                ft.ListTile(
                    title=ft.Text("Completed habits", color=TEXT_PRIMARY),
                    trailing=ft.Text(
                        str(totals["completed_habits"]),
                        color=TEXT_PRIMARY,
                        weight=ft.FontWeight.BOLD,
                    ),
                ),
            ],
        ),
    )
