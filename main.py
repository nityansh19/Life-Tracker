import flet as ft

from app.application import ArcApplication


def main(page: ft.Page) -> None:
    ArcApplication(page)


if __name__ == "__main__":
    ft.run(main)
