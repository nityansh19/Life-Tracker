from __future__ import annotations

import flet as ft

from app.utils.constants import CARD_BG


def build_navigation(selected_index: int, on_change) -> ft.NavigationBar:
    return ft.NavigationBar(
        selected_index=selected_index,
        bgcolor=CARD_BG,
        indicator_color="#2B2451",
        on_change=on_change,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME_OUTLINED, selected_icon=ft.Icons.HOME, label="Home"),
            ft.NavigationBarDestination(icon=ft.Icons.CALENDAR_MONTH_OUTLINED, selected_icon=ft.Icons.CALENDAR_MONTH, label="Calendar"),
            ft.NavigationBarDestination(icon=ft.Icons.INSIGHTS_OUTLINED, selected_icon=ft.Icons.INSIGHTS, label="Progress"),
            ft.NavigationBarDestination(icon=ft.Icons.EMOJI_EVENTS_OUTLINED, selected_icon=ft.Icons.EMOJI_EVENTS, label="Awards"),
            ft.NavigationBarDestination(icon=ft.Icons.PERSON_OUTLINED, selected_icon=ft.Icons.PERSON, label="Profile"),
        ],
    )
