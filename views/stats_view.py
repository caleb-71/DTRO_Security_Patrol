import flet as ft
from database.db_manager import get_all_records


def StatsView(page: ft.Page):
    records     = get_all_records()
    total_count = len(records)

    # ✅ 경비순찰 구역별 통계
    stats_data = {
        "관리동":              0,
        "유치선/외곽울타리":    0,
        "출고검사장/창고/배수로": 0,
    }
    for row in records:
        w_type = row[6]
        if w_type in stats_data:
            stats_data[w_type] += 1

    summary_card = ft.Container(
        content=ft.Column([
            ft.Text("누적 순찰 점검 건수", size=16,
                    color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE)),
            ft.Text(f"{total_count} 건", size=35,
                    weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
        ], alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=ft.Colors.BLUE_800,
        padding=ft.Padding(20, 20, 20, 20),
        border_radius=15, width=float("inf"),
    )

    stats_list = ft.Column(spacing=10)
    colors = [ft.Colors.BLUE_500, ft.Colors.TEAL_500, ft.Colors.INDIGO_500]
    for idx, (w_type, count) in enumerate(stats_data.items()):
        ratio = (count / total_count) if total_count > 0 else 0
        stats_list.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(w_type, weight=ft.FontWeight.BOLD),
                        ft.Text(f"{count}건"),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.ProgressBar(
                        value=ratio,
                        color=colors[idx % len(colors)],
                        bgcolor=ft.Colors.BLUE_100,
                        height=10,
                    ),
                ]),
                padding=ft.Padding(15, 15, 15, 15),
                bgcolor=ft.Colors.WHITE, border_radius=10,
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
            content=ft.Text("순찰 통계 대시보드", size=20, weight=ft.FontWeight.BOLD),
            padding=ft.Padding(left=20, top=20, right=0, bottom=10),
        ),
        ft.Container(content=summary_card,
                     padding=ft.Padding(left=20, top=0, right=20, bottom=0)),
        ft.Container(content=stats_list,
                     padding=ft.Padding(20, 20, 20, 20), expand=True),
    ], expand=True, scroll=ft.ScrollMode.AUTO)