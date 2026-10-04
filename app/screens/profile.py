import flet as ft

from app.services.analytics_service import AnalyticsService
from app.services.database import Database
from app.services.settings_service import SettingsService
from app.services.streak_service import StreakService
from app.services.user_service import UserService
from app.services.xp_service import XpService
from app.utils.constants import ACCENT, APP_BG, APP_VERSION, BORDER, CARD_BG, STREAK, TEXT_MUTED, TEXT_PRIMARY


def build_profile_screen(
    page: ft.Page,
    database: Database,
    streaks: StreakService,
    on_manage_habits,
    on_refresh,
    account_email: str = "",
    plan: str = "free",
    cloud_status: str = "Synced",
    on_sync=None,
    on_logout=None,
) -> ft.Control:
    user_service = UserService(database)
    settings = SettingsService(database)
    user = user_service.get()
    totals = AnalyticsService(database).totals()
    streak = streaks.snapshot()
    xp = XpService(database).snapshot()

    def edit_profile(e=None) -> None:
        name_field = ft.TextField(label="Name", value=user["name"], max_length=40)
        start_field = ft.TextField(label="Journey start date", value=user["journey_start_date"])
        error = ft.Text("", color="#FF6B72", size=12)

        def save(ev=None) -> None:
            try:
                user_service.update_profile(name_field.value or "", start_field.value or "")
            except ValueError as exc:
                error.value = str(exc)
                error.update()
                return
            page.pop_dialog()
            on_refresh()

        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Edit profile"),
                content=ft.Column(
                    width=360,
                    tight=True,
                    spacing=12,
                    controls=[name_field, start_field, error],
                ),
                actions=[
                    ft.TextButton(content="Cancel", on_click=lambda ev: page.pop_dialog()),
                    ft.FilledButton(content="Save", on_click=save),
                ],
            )
        )

    morning = ft.Switch(label="Morning reminder preference", value=settings.get_bool("reminder_morning"))
    evening = ft.Switch(label="Evening reminder preference", value=settings.get_bool("reminder_evening"))

    def save_morning(e) -> None:
        settings.set("reminder_morning", bool(morning.value))
        on_refresh()

    def save_evening(e) -> None:
        settings.set("reminder_evening", bool(evening.value))
        on_refresh()

    morning.on_change = save_morning
    evening.on_change = save_evening

    study_hours = totals["total_study_minutes"] / 60
    plan_label = "PREMIUM" if plan.lower() == "premium" else "FREE"
    plan_color = STREAK if plan.lower() == "premium" else ACCENT

    return ft.Container(
        expand=True,
        bgcolor=APP_BG,
        padding=ft.Padding(left=18, right=18, top=24, bottom=30),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Profile", size=28, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ft.IconButton(icon=ft.Icons.EDIT_OUTLINED, tooltip="Edit profile", on_click=edit_profile),
                    ],
                ),
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
                                content=ft.Text(user["name"][0].upper(), size=26, weight=ft.FontWeight.BOLD, color="#D8D0FF"),
                            ),
                            ft.Text(user["name"], size=22, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                            ft.Text(f"{xp['title']} · Level {xp['level']}", size=13, color=TEXT_MUTED),
                            ft.ProgressBar(value=float(xp["level_progress"]), color=ACCENT, bgcolor="#24242D", height=7, border_radius=7),
                            ft.Text(f"{xp['xp']} XP · {xp['xp_to_next']} to next level", size=11, color=TEXT_MUTED),
                            ft.Text(f"Journey started {user['journey_start_date']}", size=11, color=TEXT_MUTED),
                        ],
                    ),
                ),
                ft.Container(
                    bgcolor=CARD_BG,
                    border=ft.Border.all(1, BORDER),
                    border_radius=20,
                    padding=16,
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Column(
                                        spacing=2,
                                        controls=[
                                            ft.Text("ARC ACCOUNT", size=10, color=TEXT_MUTED, weight=ft.FontWeight.BOLD),
                                            ft.Text(account_email or "Signed in", size=13, color=TEXT_PRIMARY),
                                        ],
                                    ),
                                    ft.Container(
                                        bgcolor="#201A38" if plan_label == "FREE" else "#3A2417",
                                        border_radius=20,
                                        padding=ft.Padding(left=10, right=10, top=5, bottom=5),
                                        content=ft.Text(plan_label, size=10, color=plan_color, weight=ft.FontWeight.BOLD),
                                    ),
                                ],
                            ),
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.CLOUD_DONE_OUTLINED, size=18, color=ACCENT),
                                    ft.Text(cloud_status, size=12, color=TEXT_MUTED),
                                ]
                            ),
                            ft.Text(
                                "Premium upgrades are coming later. Core tracking and cloud backup remain available on the free plan.",
                                size=11,
                                color=TEXT_MUTED,
                            ),
                            ft.Row(
                                controls=[
                                    ft.OutlinedButton(
                                        content="Sync now",
                                        icon=ft.Icons.SYNC,
                                        on_click=on_sync,
                                    ),
                                    ft.TextButton(
                                        content="Log out",
                                        icon=ft.Icons.LOGOUT,
                                        on_click=on_logout,
                                    ),
                                ]
                            ),
                        ],
                    ),
                ),
                ft.Row(
                    controls=[
                        _stat("Current streak", f"{streak['current_streak']}d"),
                        _stat("Best streak", f"{streak['longest_streak']}d"),
                    ]
                ),
                ft.Row(
                    controls=[
                        _stat("Perfect days", str(totals["perfect_days"])),
                        _stat("Habits done", str(totals["completed_habits"])),
                    ]
                ),
                ft.Row(
                    controls=[
                        _stat("Total steps", f"{totals['total_steps']:,}"),
                        _stat("Study", f"{study_hours:.1f}h"),
                    ]
                ),
                ft.Row(controls=[_stat("Workouts", str(totals["total_workouts"]))]),
                ft.FilledButton(content="Manage habits & targets", icon=ft.Icons.TUNE, on_click=lambda e: on_manage_habits()),
                ft.Container(
                    bgcolor=CARD_BG,
                    border=ft.Border.all(1, BORDER),
                    border_radius=20,
                    padding=16,
                    content=ft.Column(
                        spacing=8,
                        controls=[
                            ft.Text("Reminder preferences", weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                            morning,
                            evening,
                            ft.Text(
                                "Preferences sync with your ARC state. Native scheduled notifications can be added in the premium/notification phase later.",
                                size=11,
                                color=TEXT_MUTED,
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    bgcolor=CARD_BG,
                    border=ft.Border.all(1, BORDER),
                    border_radius=20,
                    padding=16,
                    content=ft.Column(
                        spacing=5,
                        controls=[
                            ft.Text("Offline first + cloud backed", weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                            ft.Text(
                                "ARC keeps a local SQLite copy for speed and offline use, then backs your account state up to Supabase when online.",
                                size=12,
                                color=TEXT_MUTED,
                            ),
                            ft.Text(f"ARC {APP_VERSION}", size=11, color=TEXT_MUTED),
                        ],
                    ),
                ),
            ],
        ),
    )


def _stat(label: str, value: str) -> ft.Control:
    return ft.Container(
        expand=True,
        bgcolor=CARD_BG,
        border=ft.Border.all(1, BORDER),
        border_radius=18,
        padding=15,
        content=ft.Column(
            spacing=3,
            controls=[
                ft.Text(label.upper(), size=9, color=TEXT_MUTED, weight=ft.FontWeight.BOLD),
                ft.Text(value, size=20, color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
            ],
        ),
    )
