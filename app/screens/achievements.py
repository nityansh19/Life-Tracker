import flet as ft

from app.services.achievement_service import AchievementService
from app.services.database import Database
from app.utils.constants import APP_BG, BORDER, CARD_BG, STREAK, TEXT_MUTED, TEXT_PRIMARY


def build_achievements_screen(database: Database) -> ft.Control:
    achievements = AchievementService(database).list_all()
    unlocked_count = sum(1 for item in achievements if bool(item["unlocked"]))
    cards = []
    for item in achievements:
        unlocked = bool(item["unlocked"])
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
                                ft.Text(item["title"], size=16, color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
                                ft.Text(item["description"], size=12, color=TEXT_MUTED),
                                ft.Text("Unlocked · +50 XP" if unlocked else "Locked", size=10, color=STREAK if unlocked else TEXT_MUTED),
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
                ft.Text(f"{unlocked_count} / {len(achievements)} unlocked", size=14, color=TEXT_MUTED),
                *cards,
            ],
        ),
    )
