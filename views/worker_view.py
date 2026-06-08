import flet as ft
from database.db_manager import add_worker, get_all_workers, delete_worker, get_records_by_manager


def WorkerView(page: ft.Page):
    name_input = ft.TextField(label="이름", expand=1, height=40, border_radius=10)
    dept_input = ft.TextField(label="소속/부서 (선택)", expand=1, height=40, border_radius=10)

    worker_list_view = ft.ListView(
        expand=True, spacing=10,
        padding=ft.Padding(10, 10, 10, 10),
    )

    # ==========================================
    # 🌟 작업자 점검 이력 BottomSheet — 미리 조립
    # ==========================================
    _history_col = ft.Column(
        scroll=ft.ScrollMode.AUTO,
        spacing=8,
        expand=True,
    )

    def _close_history(e):
        history_sheet.open = False
        page.update()

    history_sheet = ft.BottomSheet(
        open=False,
        content=ft.Container(
            padding=ft.Padding(20, 16, 20, 30),
            content=ft.Column(
                tight=True,
                spacing=8,
                controls=[
                    ft.Row([
                        ft.Icon(ft.Icons.HISTORY, color=ft.Colors.BLUE_800),
                        ft.Text(
                            "점검 이력",
                            size=17, weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLUE_800,
                        ),
                        ft.Container(expand=True),
                        ft.TextButton("닫기", on_click=_close_history),
                    ]),
                    ft.Divider(height=4),
                    ft.Container(
                        content=_history_col,
                        height=380,
                    ),
                ],
            ),
        ),
    )

    page.overlay.append(history_sheet)

    # ==========================================
    # 🌟 작업자 클릭 → 이력 BottomSheet 열기
    # ==========================================
    def show_worker_history(manager_name):
        history_records = get_records_by_manager(manager_name)

        _history_col.controls.clear()
        _history_col.controls.append(
            ft.Text(
                f"👷 [{manager_name}] 안전 점검 이력",
                size=15, weight=ft.FontWeight.BOLD,
                color=ft.Colors.BLUE_800,
            )
        )
        _history_col.controls.append(ft.Divider(height=1))

        if not history_records:
            _history_col.controls.append(
                ft.Text("과거 점검 기록이 없습니다.", color=ft.Colors.GREY_500, size=13)
            )
        else:
            for row in history_records:
                task_name = row[1]
                task_date = row[2]
                work_type = row[6]
                _history_col.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                f"[{work_type}] {task_name}",
                                weight=ft.FontWeight.BOLD, size=14,
                            ),
                            ft.Text(
                                f"일자: {task_date}",
                                size=12, color=ft.Colors.GREY_600,
                            ),
                        ], spacing=3),
                        padding=ft.Padding(10, 10, 10, 10),
                        bgcolor=ft.Colors.BLUE_GREY_50,
                        border_radius=8,
                    )
                )

        history_sheet.open = True
        page.update()

    # ==========================================
    # 🌟 작업자 목록 갱신
    # ==========================================
    def update_worker_list():
        worker_list_view.controls.clear()
        workers = get_all_workers()

        if not workers:
            worker_list_view.controls.append(
                ft.Container(
                    content=ft.Text(
                        "등록된 작업자가 없습니다. 상단에서 등록해 주세요.",
                        color=ft.Colors.GREY_500,
                    ),
                    alignment=ft.Alignment(0, 0),
                    padding=ft.Padding(30, 30, 30, 30),
                )
            )
        else:
            for w in workers:
                w_id, w_name, w_dept, _ = w

                def create_click_event(name):
                    return lambda _: show_worker_history(name)

                def create_delete_event(worker_id, name):
                    def delete_click(e):
                        delete_worker(worker_id)
                        update_worker_list()
                        page.snack_bar = ft.SnackBar(
                            ft.Text(f"{name} 작업자가 삭제되었습니다."),
                            bgcolor=ft.Colors.GREY_700,
                        )
                        page.snack_bar.open = True
                        page.update()
                    return delete_click

                worker_list_view.controls.append(
                    ft.Card(
                        content=ft.ListTile(
                            leading=ft.CircleAvatar(
                                content=ft.Text(w_name[0] if w_name else "작"),
                                bgcolor=ft.Colors.BLUE_100,
                                color=ft.Colors.BLUE_800,
                            ),
                            title=ft.Text(w_name, weight=ft.FontWeight.BOLD),
                            subtitle=ft.Text(f"소속: {w_dept}"),
                            trailing=ft.IconButton(
                                ft.Icons.DELETE_OUTLINE,
                                icon_color=ft.Colors.RED_400,
                                on_click=create_delete_event(w_id, w_name),
                            ),
                            on_click=create_click_event(w_name),
                        )
                    )
                )
        page.update()

    # ==========================================
    # 🌟 작업자 등록
    # ==========================================
    def add_new_worker(e):
        if not name_input.value:
            page.snack_bar = ft.SnackBar(
                ft.Text("이름을 입력하세요!"),
                bgcolor=ft.Colors.RED_ACCENT,
            )
            page.snack_bar.open = True
            page.update()
            return

        add_worker(name_input.value, dept_input.value or "미지정", "")
        name_input.value = ""
        dept_input.value = ""
        update_worker_list()

    update_worker_list()

    # ==========================================
    # 🌟 화면 조립
    # ==========================================
    return ft.Column([
        ft.Container(
            content=ft.Text("현장 인력 관리", size=20, weight=ft.FontWeight.BOLD),
            padding=ft.Padding(left=20, top=20, right=0, bottom=10),
        ),
        ft.Container(
            content=ft.Column([
                ft.Row([name_input, dept_input], spacing=5),
                ft.ElevatedButton(
                    content=ft.Text("등록", color=ft.Colors.WHITE),
                    on_click=add_new_worker,
                    bgcolor=ft.Colors.BLUE_800,
                    height=40,
                    width=float("inf"),
                ),
            ], spacing=5),
            padding=ft.Padding(15, 15, 15, 15),
            margin=ft.Margin(left=20, top=0, right=20, bottom=0),
            border=ft.Border(
                top=ft.BorderSide(1, ft.Colors.BLACK12),
                bottom=ft.BorderSide(1, ft.Colors.BLACK12),
                left=ft.BorderSide(1, ft.Colors.BLACK12),
                right=ft.BorderSide(1, ft.Colors.BLACK12),
            ),
            border_radius=12,
            bgcolor=ft.Colors.WHITE,
        ),
        ft.Divider(),
        ft.Container(
            content=worker_list_view,
            padding=ft.Padding(left=10, top=0, right=10, bottom=0),
            expand=True,
        ),
    ], expand=True)