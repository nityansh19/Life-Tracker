from __future__ import annotations

import flet as ft

from app.utils.constants import APP_BG, BORDER, CARD_BG, DANGER, SUCCESS, TEXT_MUTED, TEXT_PRIMARY


def build_auth_screen(page: ft.Page, mode: str, on_back, on_switch, on_login, on_signup) -> ft.Control:
    is_signup = mode == "signup"
    name = ft.TextField(label="Name", visible=is_signup, max_length=40)
    email = ft.TextField(label="Email", keyboard_type=ft.KeyboardType.EMAIL)
    password = ft.TextField(label="Password", password=True, can_reveal_password=True)
    status = ft.Text("", size=12)
    submit = ft.FilledButton(
        content="Create account" if is_signup else "Sign in",
        icon=ft.Icons.PERSON_ADD_ALT_1 if is_signup else ft.Icons.LOGIN,
    )

    async def handle_submit(e=None) -> None:
        status.value = ""
        submit.disabled = True
        submit.content = "Creating account..." if is_signup else "Signing in..."
        page.update()

        if not (email.value or "").strip() or not password.value:
            result = None
            status.value = "Enter your email and password."
            status.color = DANGER
        elif is_signup:
            result = await on_signup(name.value or "", email.value or "", password.value or "")
        else:
            result = await on_login(email.value or "", password.value or "")

        if result is not None:
            status.value = result.message
            status.color = SUCCESS if result.ok else DANGER

        submit.disabled = False
        submit.content = "Create account" if is_signup else "Sign in"
        page.update()

    submit.on_click = handle_submit

    return ft.Container(
        expand=True,
        bgcolor=APP_BG,
        padding=ft.Padding(left=22, right=22, top=24, bottom=30),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=18,
            controls=[
                ft.Row(
                    controls=[
                        ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: on_back()),
                        ft.Text("ARC Account", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ]
                ),
                ft.Container(
                    bgcolor=CARD_BG,
                    border=ft.Border.all(1, BORDER),
                    border_radius=26,
                    padding=22,
                    content=ft.Column(
                        spacing=14,
                        controls=[
                            ft.Icon(ft.Icons.CLOUD_DONE_OUTLINED, size=42, color="#7C5CFC"),
                            ft.Text(
                                "Create your account" if is_signup else "Welcome back",
                                size=28,
                                weight=ft.FontWeight.BOLD,
                                color=TEXT_PRIMARY,
                            ),
                            ft.Text(
                                "Your habits work offline and sync to your private cloud backup when you are online.",
                                size=13,
                                color=TEXT_MUTED,
                            ),
                            name,
                            email,
                            password,
                            ft.Text(
                                "Use at least 8 characters." if is_signup else "Your session is stored using Android secure storage.",
                                size=11,
                                color=TEXT_MUTED,
                            ),
                            status,
                            submit,
                            ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    ft.Text(
                                        "Already have an account?" if is_signup else "New to ARC?",
                                        size=12,
                                        color=TEXT_MUTED,
                                    ),
                                    ft.TextButton(
                                        content="Sign in" if is_signup else "Create account",
                                        on_click=lambda e: on_switch("login" if is_signup else "signup"),
                                    ),
                                ],
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )
