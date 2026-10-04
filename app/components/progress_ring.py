import flet as ft

from app.utils.constants import ACCENT, TEXT_MUTED, TEXT_PRIMARY


def progress_ring(completed: int, total: int, percentage: float) -> ft.Control:
    value = min(max(percentage / 100, 0), 1)
    return ft.Stack(
        width=176,
        height=176,
        alignment=ft.Alignment.CENTER,
        controls=[
            ft.ProgressRing(
                value=value,
                stroke_width=12,
                color=ACCENT,
                bgcolor="#24242D",
                width=176,
                height=176,
            ),
            ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
                controls=[
                    ft.Text(f"{round(percentage)}%", size=32, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Text(f"{completed} / {total} goals", size=13, color=TEXT_MUTED),
                ],
            ),
        ],
    )
