import flet as ft

from app.services.database import Database
from app.services.streak_service import StreakService
from app.utils.constants import APP_BG, BORDER, CARD_BG, STREAK, TEXT_MUTED, TEXT_PRIMARY


ACHIEVEMENTS = [
    ("First Flame", "Complete your first perfect day", 1),
    ("One Week Strong", "Reach a 7-day streak", 7),
    ("Locked In", "Reach a 14-day streak", 14),
    ("Discipline", "Reach a 30-day streak", 30),
    ("Unstoppable", "Reach a 100-day streak", 100),
]


def build_achievements_screen(database: Database, streaks: StreakService) -> ft.Control:
    streak = streaks.snapshot()
    best = int(streak["longest_streak"])
    cards = []
    for title, description, requirement in ACHIEVEMENTS:
        unlocked = best >= requirement or (
            requirement == 1 and int(streak["total_completed_days"]) >= 1
        )
        cards.append(
            ft.Container(
                bgcolor=CARD_BG,
                border=ft.Border.all(1, BORDER),
                border_radius=20,
                padding=18,
                content=ft.Row(
                    controls=[
                        ft.Container(
                            width=48,
                            height=48,
                            border_radius=16,
                            bgcolor="#3A2417" if unlocked else "#202026",
                            alignment=ft.Alignment.CENTER,
                            content=ft.Icon(
                                ft.Icons.LOCAL_FIRE_DEPARTMENT if unlocked else ft.Icons.LOCK_OUTLINE,
                                color=STREAK if unlocked else TEXT_MUTED,
                            ),
                        ),
                        ft.Column(
                            expand=True,
                            spacing=3,
                            controls=[
                                ft.Text(title, size=16, color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
                                ft.Text(description, size=12, color=TEXT_MUTED),
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
                ft.Text("Achievements", size=28, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text("Milestones earned through consistency.", size=14, color=TEXT_MUTED),
                *cards,
            ],
        ),
    )
