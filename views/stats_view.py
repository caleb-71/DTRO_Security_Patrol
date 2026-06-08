import flet as ft
from database.db_manager import get_all_records


def StatsView(page: ft.Page):
    # DB에서 실제 데이터 가져오기
    records = get_all_records()
    total_count = len(records)

    # 작업 종류별 카운트
    stats_data = {
        "아크용접": 0,
        "가스용접": 0,
        "플라즈마": 0,
        "테르밋용접": 0,
        "그라인더/금속절단기": 0,
    }
    for row in records:
        w_type = row[6]
        if w_type in stats_data:
            stats_data[w_type] += 1

    # 총 점검 건수 요약 카드
    summary_card = ft.Container(
        content=ft.Column([
            ft.Text(
                "누적 안전 점검 건수",
                size=16,
                color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
            ),
            ft.Text(
                f"{total_count} 건",
                size=35,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE,
            ),
        ], alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=ft.Colors.BLUE_800,
        padding=ft.Padding(20, 20, 20, 20),
        border_radius=15,
        width=float("inf"),
    )

    # 작업별 통계 바 리스트
    stats_list = ft.Column(spacing=10)
    for w_type, count in stats_data.items():
        ratio = (count / total_count) if total_count > 0 else 0
        stats_list.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Row(
                        [
                            ft.Text(w_type, weight=ft.FontWeight.BOLD),
                            ft.Text(f"{count}건"),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.ProgressBar(
                        value=ratio,
                        color=ft.Colors.BLUE_500,
                        bgcolor=ft.Colors.BLUE_100,
                        height=10,
                    ),
                ]),
                padding=ft.Padding(15, 15, 15, 15),
                bgcolor=ft.Colors.WHITE,
                border_radius=10,
                border=ft.Border(
                    top=ft.BorderSide(1, ft.Colors.BLACK12),
                    bottom=ft.BorderSide(1, ft.Colors.BLACK12),
                    left=ft.BorderSide(1, ft.Colors.BLACK12),
                    right=ft.BorderSide(1, ft.Colors.BLACK12),
                ),
            )
        )

    return ft.Column([
        ft.Container(
            content=ft.Text("점검 통계 대시보드", size=20, weight=ft.FontWeight.BOLD),
            padding=ft.Padding(left=20, top=20, right=0, bottom=10),
        ),
        ft.Container(
            content=summary_card,
            padding=ft.Padding(left=20, top=0, right=20, bottom=0),
        ),
        ft.Container(
            content=stats_list,
            padding=ft.Padding(20, 20, 20, 20),
            expand=True,
        ),
    ], expand=True, scroll=ft.ScrollMode.AUTO)