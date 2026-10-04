from __future__ import annotations

import flet as ft

from app.utils.constants import ACCENT, APP_BG, BORDER, CARD_BG, STREAK, TEXT_MUTED, TEXT_PRIMARY


FEATURES = (
    ("Daily Mission", "Track required and optional habits with a clear daily completion target.", ft.Icons.CHECK_CIRCLE_OUTLINE),
    ("Streaks & XP", "Build streaks, earn XP and unlock achievements as your consistency grows.", ft.Icons.LOCAL_FIRE_DEPARTMENT),
    ("Calendar History", "Open any past day and see exactly what you completed or missed.", ft.Icons.CALENDAR_MONTH),
    ("Analytics", "See weekly and monthly completion, steps, water, study and workout consistency.", ft.Icons.INSIGHTS),
    ("Weekly Report", "Get a simple weekly self-improvement report and compare it with last week.", ft.Icons.SUMMARIZE_OUTLINED),
    ("Cloud Backup", "Sign in to keep your ARC data backed up and available across devices.", ft.Icons.CLOUD_DONE_OUTLINED),
)


def build_preview_screen(on_start, on_sign_in) -> ft.Control:
    cards = [
        ft.Container(
            bgcolor=CARD_BG,
            border=ft.Border.all(1, BORDER),
            border_radius=20,
            padding=18,
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Container(
                        width=46,
                        height=46,
                        border_radius=15,
                        bgcolor="#201A38",
                        alignment=ft.Alignment.CENTER,
                        content=ft.Icon(icon, color=ACCENT),
                    ),
                    ft.Column(
                        expand=True,
                        spacing=4,
                        controls=[
                            ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                            ft.Text(description, size=12, color=TEXT_MUTED),
                        ],
                    ),
                ],
            ),
        )
        for title, description, icon in FEATURES
    ]

    return ft.Container(
        expand=True,
        bgcolor=APP_BG,
        padding=ft.Padding(left=22, right=22, top=30, bottom=30),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=18,
            controls=[
                ft.Container(
                    padding=ft.Padding(top=14, bottom=14, left=0, right=0),
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.AUTO_AWESOME, color=ACCENT, size=28),
                                    ft.Text("ARC", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                                ]
                            ),
                            ft.Text(
                                "Build the person you said you wanted to become.",
                                size=34,
                                weight=ft.FontWeight.BOLD,
                                color=TEXT_PRIMARY,
                            ),
                            ft.Text(
                                "Explore what ARC can do before creating an account. Sign in only when you want to start tracking.",
                                size=14,
                                color=TEXT_MUTED,
                            ),
                            ft.Row(
                                controls=[
                                    ft.FilledButton(
                                        content="Start using ARC",
                                        icon=ft.Icons.ARROW_FORWARD,
                                        on_click=lambda e: on_start(),
                                    ),
                                    ft.TextButton(
                                        content="Sign in",
                                        on_click=lambda e: on_sign_in(),
                                    ),
                                ]
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    bgcolor="#17131F",
                    border_radius=20,
                    padding=16,
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.WORKSPACE_PREMIUM_OUTLINED, color=STREAK),
                            ft.Column(
                                expand=True,
                                spacing=2,
                                controls=[
                                    ft.Text("Free core experience", color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
                                    ft.Text(
                                        "Premium is planned for later. Your account already supports future upgrades.",
                                        size=12,
                                        color=TEXT_MUTED,
                                    ),
                                ],
                            ),
                        ]
                    ),
                ),
                ft.Text("What you get", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                *cards,
                ft.FilledButton(
                    content="Create your free ARC account",
                    icon=ft.Icons.PERSON_ADD_ALT_1,
                    on_click=lambda e: on_start(),
                ),
            ],
        ),
    )
