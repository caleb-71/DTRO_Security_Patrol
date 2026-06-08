import flet as ft

from database.db_manager import init_db
from views.checklist_view import ChecklistView
from views.history_view import HistoryView
from views.worker_view import WorkerView
from views.stats_view import StatsView
from views.settings_view import SettingsView


async def main(page: ft.Page):
    init_db()

    # 1. SharedPreferences 등록
    sp = ft.SharedPreferences()
    page.services.append(sp)

    page.title   = "DTRO 경비순찰"
    page.padding = 0
    page.window_width  = 450
    page.window_height = 800

    # 2. 테마 설정
    #    Android 기본 한글 폰트(Noto Sans KR)를 그대로 사용
    #    → 별도 폰트 등록 불필요, 기본 폰트가 더 자연스러움
    saved_theme = await sp.get("theme")
    page.theme_mode = ft.ThemeMode.DARK if saved_theme == "dark" else ft.ThemeMode.LIGHT

    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.BLUE_800,
    )
    page.dark_theme = ft.Theme(
        color_scheme_seed=ft.Colors.BLUE_800,
    )

    # 4. AppBar
    page.appbar = ft.AppBar(
        leading=ft.Icon(ft.Icons.SHIELD_OUTLINED, color=ft.Colors.WHITE),
        leading_width=40,
        title=ft.Text(
            "경비순찰 체크리스트",
            color=ft.Colors.WHITE,
            weight=ft.FontWeight.BOLD,
        ),
        bgcolor=ft.Colors.BLUE_800,
        center_title=False,
    )

    # 5. 탭 전환
    main_container = ft.Container(expand=True, content=ChecklistView(page))

    def change_tab(e):
        idx = e.control.selected_index
        views = {
            0: ChecklistView,
            1: HistoryView,
            2: WorkerView,
            3: StatsView,
            4: SettingsView,
        }
        main_container.content = views[idx](page)
        page.update()

    # 6. 하단 내비게이션 바
    page.navigation_bar = ft.NavigationBar(
        selected_index=0,
        on_change=change_tab,
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.Icons.FACT_CHECK_OUTLINED,
                selected_icon=ft.Icons.FACT_CHECK,
                label="체크리스트",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.HISTORY_OUTLINED,
                selected_icon=ft.Icons.HISTORY,
                label="기록조회",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.PEOPLE_OUTLINE,
                selected_icon=ft.Icons.PEOPLE,
                label="작업자",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.BAR_CHART_OUTLINED,
                selected_icon=ft.Icons.INSERT_CHART,
                label="통계",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.SETTINGS_OUTLINED,
                selected_icon=ft.Icons.SETTINGS,
                label="설정",
            ),
        ],
    )

    page.add(ft.Column([main_container], expand=True))
    page.update()


if __name__ == "__main__":
    ft.run(main)