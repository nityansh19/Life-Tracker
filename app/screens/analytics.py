import flet as ft

from app.services.analytics_service import AnalyticsService
from app.services.database import Database
from app.services.streak_service import StreakService
from app.utils.constants import ACCENT, APP_BG, BORDER, CARD_BG, SUCCESS, TEXT_MUTED, TEXT_PRIMARY


def _metric(label: str, value: str, subtitle: str = "") -> ft.Control:
    return ft.Container(
        expand=True,
        bgcolor=CARD_BG,
        border=ft.Border.all(1, BORDER),
        border_radius=20,
        padding=17,
        content=ft.Column(
            spacing=4,
            controls=[
                ft.Text(label.upper(), size=10, color=TEXT_MUTED, weight=ft.FontWeight.BOLD),
                ft.Text(value, size=24, color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
                ft.Text(subtitle, size=11, color=TEXT_MUTED) if subtitle else ft.Container(height=0),
            ],
        ),
    )


def _duration(minutes: int) -> str:
    hours, mins = divmod(minutes, 60)
    return f"{hours}h {mins:02d}m" if hours else f"{mins}m"


def build_analytics_screen(database: Database, streaks: StreakService) -> ft.Control:
    analytics = AnalyticsService(database)
    weekly = analytics.completion_rate(7)
    monthly = analytics.completion_rate(30)
    totals = analytics.totals()
    averages = analytics.averages(7)
    workout = analytics.workout_consistency(30)
    report = analytics.weekly_report()
    streak = streaks.snapshot()

    return ft.Container(
        expand=True,
        bgcolor=APP_BG,
        padding=ft.Padding(left=18, right=18, top=24, bottom=30),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                ft.Text("Progress", size=28, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text("Your consistency, without noise.", size=14, color=TEXT_MUTED),
                ft.Container(
                    bgcolor=CARD_BG,
                    border_radius=24,
                    border=ft.Border.all(1, BORDER),
                    padding=20,
                    content=ft.Column(
                        spacing=12,
                        controls=[
                            ft.Text("7-DAY COMPLETION", size=11, color=TEXT_MUTED, weight=ft.FontWeight.BOLD),
                            ft.Text(f"{weekly}%", size=38, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                            ft.ProgressBar(value=weekly / 100, color=ACCENT, bgcolor="#24242D", height=9, border_radius=9),
                            ft.Text(f"30-day completion: {monthly}%", size=12, color=TEXT_MUTED),
                        ],
                    ),
                ),
                ft.Row(controls=[_metric("Current streak", f"{streak['current_streak']}d"), _metric("Best streak", f"{streak['longest_streak']}d")]),
                ft.Row(controls=[_metric("Perfect days", str(totals["perfect_days"])), _metric("Missed days", str(totals["missed_days"]))]),
                ft.Text("7-day averages", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Row(controls=[_metric("Steps", f"{int(averages['steps']):,}"), _metric("Water", f"{averages['water_ml'] / 1000:.1f}L")]),
                ft.Row(controls=[_metric("Study", _duration(int(averages["study_minutes"]))), _metric("Workout", f"{workout}%", "30-day consistency")]),
                ft.Text("This week", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(
                    bgcolor=CARD_BG,
                    border=ft.Border.all(1, BORDER),
                    border_radius=24,
                    padding=18,
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Text("WEEKLY SELF-IMPROVEMENT REPORT", size=11, color=TEXT_MUTED, weight=ft.FontWeight.BOLD),
                            ft.Text(f"Goals completed · {report['completion_percentage']}%", size=19, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Workouts", color=TEXT_MUTED), ft.Text(str(report["workouts"]), color=TEXT_PRIMARY)]),
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Average steps", color=TEXT_MUTED), ft.Text(f"{report['average_steps']:,}", color=TEXT_PRIMARY)]),
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Average water", color=TEXT_MUTED), ft.Text(f"{report['average_water_ml'] / 1000:.1f}L", color=TEXT_PRIMARY)]),
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Study", color=TEXT_MUTED), ft.Text(_duration(report["study_minutes"]), color=TEXT_PRIMARY)]),
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Perfect days", color=TEXT_MUTED), ft.Text(str(report["perfect_days"]), color=SUCCESS)]),
                            ft.Divider(),
                            ft.Text(report["message"], color=TEXT_MUTED, size=12),
                        ],
                    ),
                ),
            ],
        ),
    )
