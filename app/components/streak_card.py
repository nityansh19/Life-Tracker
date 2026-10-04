import flet as ft

from app.utils.constants import STREAK, STREAK_SOFT, TEXT_MUTED, TEXT_PRIMARY


def streak_card(current: int, best: int) -> ft.Control:
    return ft.Container(
        padding=18,
        border_radius=24,
        bgcolor=STREAK_SOFT,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(
                            width=48,
                            height=48,
                            border_radius=16,
                            bgcolor="#51301B",
                            alignment=ft.Alignment.CENTER,
                            content=ft.Icon(ft.Icons.LOCAL_FIRE_DEPARTMENT, color=STREAK, size=28),
                        ),
                        ft.Column(
                            spacing=1,
                            controls=[
                                ft.Text("CURRENT STREAK", size=11, color=TEXT_MUTED, weight=ft.FontWeight.BOLD),
                                ft.Text(f"{current} days", size=25, color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
                            ],
                        ),
                    ]
                ),
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.END,
                    spacing=1,
                    controls=[
                        ft.Text("BEST", size=11, color=TEXT_MUTED, weight=ft.FontWeight.BOLD),
                        ft.Text(f"{best}", size=22, color=STREAK, weight=ft.FontWeight.BOLD),
                    ],
                ),
            ],
        ),
    )
