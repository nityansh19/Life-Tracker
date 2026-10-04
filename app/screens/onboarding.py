import flet as ft

from app.utils.constants import ACCENT, APP_BG, TEXT_MUTED, TEXT_PRIMARY


def build_onboarding_screen(on_start) -> ft.Control:
    """Reserved onboarding view for the later personalization phase."""
    return ft.Container(
        expand=True,
        bgcolor=APP_BG,
        padding=28,
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            controls=[
                ft.Icon(ft.Icons.AUTO_AWESOME, size=48, color=ACCENT),
                ft.Text("BUILD YOUR ARC", size=30, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text("Small habits. Every day.", size=15, color=TEXT_MUTED),
                ft.FilledButton(content="Start journey", on_click=on_start),
            ],
        ),
    )
