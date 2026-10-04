from __future__ import annotations

from datetime import date, datetime

import flet as ft

from app.services.database import Database
from app.services.settings_service import SettingsService
from app.services.user_service import UserService
from app.utils.constants import ACCENT, APP_BG, BORDER, CARD_BG, TEXT_MUTED, TEXT_PRIMARY


def build_onboarding_screen(
    page: ft.Page,
    database: Database,
    settings: SettingsService,
    on_finish,
) -> ft.Control:
    user_service = UserService(database)
    user = user_service.get()
    with database.connection() as connection:
        starter_rows = connection.execute("SELECT id, name, category, active FROM habits ORDER BY id").fetchall()

    step = [0]
    name_field = ft.TextField(label="Your name", value=user["name"], max_length=40)
    start_field = ft.TextField(
        label="Journey start date",
        value=date.today().isoformat(),
        hint_text="YYYY-MM-DD",
    )
    selected_ids = {int(row["id"]) for row in starter_rows if bool(row["active"])}
    error = ft.Text("", color="#FF6B72", size=12)
    host = ft.Container(expand=True)

    def choice_card(row) -> ft.Control:
        habit_id = int(row["id"])
        checkbox = ft.Checkbox(value=habit_id in selected_ids)

        def change(e) -> None:
            if checkbox.value:
                selected_ids.add(habit_id)
            else:
                selected_ids.discard(habit_id)

        checkbox.on_change = change
        return ft.Container(
            bgcolor=CARD_BG,
            border=ft.Border.all(1, BORDER),
            border_radius=18,
            padding=14,
            content=ft.Row(
                controls=[
                    checkbox,
                    ft.Column(
                        expand=True,
                        spacing=2,
                        controls=[
                            ft.Text(row["name"], weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                            ft.Text(row["category"], size=11, color=TEXT_MUTED),
                        ],
                    ),
                ]
            ),
        )

    def next_step(e=None) -> None:
        if step[0] == 0 and not (name_field.value or "").strip():
            error.value = "Enter your name to continue."
            error.update()
            return
        if step[0] == 1 and not selected_ids:
            error.value = "Choose at least one starter habit."
            error.update()
            return
        if step[0] == 2:
            try:
                parsed = date.fromisoformat(start_field.value or "")
                if parsed > date.today():
                    raise ValueError
            except ValueError:
                error.value = "Use a valid date that is not in the future."
                error.update()
                return
        error.value = ""
        step[0] = min(3, step[0] + 1)
        render_step()

    def previous_step(e=None) -> None:
        error.value = ""
        step[0] = max(0, step[0] - 1)
        render_step()

    def finish(e=None) -> None:
        try:
            parsed = date.fromisoformat(start_field.value or "")
            user_service.update_profile(name_field.value or "", parsed.isoformat())
        except ValueError as exc:
            error.value = str(exc)
            error.update()
            return

        now = datetime.now().isoformat(timespec="seconds")
        with database.connection() as connection:
            rows = connection.execute("SELECT id FROM habits").fetchall()
            for row in rows:
                habit_id = int(row["id"])
                active = habit_id in selected_ids
                connection.execute(
                    "UPDATE habits SET active = ?, archived_at = ?, updated_at = ? WHERE id = ?",
                    (int(active), None if active else now, now, habit_id),
                )
        settings.set("onboarding_complete", True)
        on_finish()

    def render_step() -> None:
        title = ft.Text("BUILD YOUR ARC", size=30, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)
        progress = ft.ProgressBar(value=(step[0] + 1) / 4, color=ACCENT, bgcolor="#24242D", height=7)

        if step[0] == 0:
            content = ft.Column(
                spacing=14,
                controls=[
                    ft.Icon(ft.Icons.AUTO_AWESOME, size=48, color=ACCENT),
                    title,
                    ft.Text("Small habits. Every day.", size=15, color=TEXT_MUTED),
                    name_field,
                ],
            )
        elif step[0] == 1:
            content = ft.Column(
                spacing=12,
                controls=[
                    title,
                    ft.Text("Choose your starting system. You can change everything later.", color=TEXT_MUTED),
                    *[choice_card(row) for row in starter_rows],
                ],
            )
        elif step[0] == 2:
            content = ft.Column(
                spacing=14,
                controls=[
                    title,
                    ft.Text("Choose when this journey officially begins.", color=TEXT_MUTED),
                    start_field,
                    ft.Text("ARC stores dates locally so streaks and history survive restarts.", size=12, color=TEXT_MUTED),
                ],
            )
        else:
            content = ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=14,
                controls=[
                    ft.Icon(ft.Icons.LOCAL_FIRE_DEPARTMENT, size=58, color="#FF9A4A"),
                    ft.Text("Your Arc Begins Today.", size=28, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Text(f"{len(selected_ids)} habits ready. One day at a time.", color=TEXT_MUTED),
                    ft.FilledButton(content="Start Journey", icon=ft.Icons.ARROW_FORWARD, on_click=finish),
                ],
            )

        buttons: list[ft.Control] = []
        if step[0] > 0 and step[0] < 3:
            buttons.append(ft.TextButton(content="Back", on_click=previous_step))
        if step[0] < 3:
            buttons.append(ft.FilledButton(content="Continue", on_click=next_step))

        host.content = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=18,
            controls=[
                progress,
                content,
                error,
                ft.Row(alignment=ft.MainAxisAlignment.END, controls=buttons),
            ],
        )
        page.update()

    render_step()
    return ft.Container(
        expand=True,
        bgcolor=APP_BG,
        padding=ft.Padding(left=24, right=24, top=30, bottom=30),
        content=host,
    )
