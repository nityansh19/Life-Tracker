import flet as ft

from app.application import ArcApplication


async def main(page: ft.Page) -> None:
    app = ArcApplication(page)
    await app.initialize()


if __name__ == "__main__":
    ft.run(main)
