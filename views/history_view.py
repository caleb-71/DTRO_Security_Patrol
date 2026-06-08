import flet as ft
import flet.canvas as cv
import json

from database.db_manager import get_all_records, delete_record
from utils.report_generator import generate_html_report
from utils.email_sender import send_report_email   # ✅ 이메일 전송 연동


def HistoryView(page: ft.Page):

    # ==========================================
    # 🌟 결과 알림 BottomSheet (이메일 전송 결과 표시)
    #    checklist_view.py 와 동일한 패턴 사용
    # ==========================================
    _r_icon  = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_700, size=28)
    _r_title = ft.Text("", size=17, weight=ft.FontWeight.BOLD)
    _r_msg   = ft.Text("", size=13, color=ft.Colors.BLUE_GREY_700)

    def _close_result(e):
        result_sheet.open = False
        page.update()

    result_sheet = ft.BottomSheet(
        open=False,
        content=ft.Container(
            padding=ft.Padding(24, 24, 24, 36),
            content=ft.Column(
                tight=True, spacing=14,
                controls=[
                    ft.Row([_r_icon, _r_title], spacing=10),
                    _r_msg,
                    ft.ElevatedButton(
                        content=ft.Text("확인", color=ft.Colors.WHITE,
                                        weight=ft.FontWeight.BOLD),
                        on_click=_close_result,
                        bgcolor=ft.Colors.BLUE_800,
                        height=46,
                        width=float("inf"),
                    ),
                ],
            ),
        ),
    )

    def _show_result(title: str, msg: str, success: bool = True):
        _r_icon.name   = ft.Icons.CHECK_CIRCLE if success else ft.Icons.ERROR_OUTLINE
        _r_icon.color  = ft.Colors.GREEN_700   if success else ft.Colors.RED_700
        _r_title.value = title
        _r_title.color = ft.Colors.GREEN_700   if success else ft.Colors.RED_700
        _r_msg.value   = msg
        result_sheet.open = True
        page.update()

    # ==========================================
    # 🌟 상세보기 BottomSheet
    # ==========================================
    detail_col   = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=10, expand=True)
    _current_rid = {"id": None}

    def _close_detail(e):
        detail_sheet.open = False
        page.update()

    def _html_from_detail(e):
        """
        기록 상세보기에서 보고서 발행 + 이메일 전송
        checklist_view.py 와 동일한 2단계 흐름:
          1단계: HTML 파일 생성 → (True, save_path) 반환
          2단계: 저장된 경로를 이메일로 전송
        """
        data = _current_rid.get("report_data")
        if not data:
            return

        # 상세보기 시트 먼저 닫기
        detail_sheet.open = False
        page.update()

        try:
            # 1단계: HTML 파일 생성
            ok, result = generate_html_report(data)

            if not ok:
                _show_result(title="발행 실패", msg=f"보고서 생성 실패:\n{result}", success=False)
                return

            html_path = result   # 저장된 파일 경로

            # 2단계: 이메일 전송
            email_ok, email_msg = send_report_email(html_path, data)

            if email_ok:
                _show_result(
                    title="발행 및 전송 완료",
                    msg="보고서가 저장되고\n관리자 이메일로 전송되었습니다.",
                    success=True,
                )
            else:
                _show_result(
                    title="보고서 저장 완료",
                    msg=f"기기에 저장되었습니다.\n(이메일 전송 실패: {email_msg})",
                    success=False,
                )

        except Exception as ex:
            _show_result(title="오류 발생", msg=f"보고서 발행 중 오류:\n{ex}", success=False)

    def _request_delete(e):
        detail_sheet.open = False
        delete_sheet.open = True
        page.update()

    detail_sheet = ft.BottomSheet(
        open=False,
        content=ft.Container(
            padding=ft.Padding(20, 16, 20, 30),
            content=ft.Column(
                tight=True,
                spacing=0,
                controls=[
                    ft.Row([
                        ft.IconButton(
                            ft.Icons.PICTURE_AS_PDF,
                            icon_color=ft.Colors.BLUE_800,
                            tooltip="HTML 보고서 발행 + 이메일 전송",
                            on_click=_html_from_detail,
                        ),
                        ft.IconButton(
                            ft.Icons.DELETE_FOREVER,
                            icon_color=ft.Colors.RED_600,
                            tooltip="기록 삭제",
                            on_click=_request_delete,
                        ),
                        ft.Container(expand=True),
                        ft.TextButton("닫기", on_click=_close_detail),
                    ]),
                    ft.Divider(height=4),
                    ft.Container(
                        content=detail_col,
                        height=480,
                        expand=False,
                    ),
                ],
            ),
        ),
    )

    # ==========================================
    # 🌟 삭제 확인 BottomSheet
    # ==========================================
    def _confirm_delete(e):
        rid = _current_rid.get("id")
        if rid is not None:
            delete_record(rid)
        delete_sheet.open = False
        page.snack_bar = ft.SnackBar(
            ft.Text("기록이 삭제되었습니다."),
            bgcolor=ft.Colors.GREY_700,
        )
        page.snack_bar.open = True
        refresh_data()
        page.update()

    def _cancel_delete(e):
        delete_sheet.open = False
        page.update()

    delete_sheet = ft.BottomSheet(
        open=False,
        content=ft.Container(
            padding=ft.Padding(24, 24, 24, 36),
            content=ft.Column(
                tight=True,
                spacing=16,
                controls=[
                    ft.Row([
                        ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED,
                                color=ft.Colors.RED_600, size=24),
                        ft.Text("기록 삭제", size=18,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.RED_600),
                    ], spacing=8),
                    ft.Text(
                        "이 점검 기록을 영구 삭제하시겠습니까?\n삭제 후에는 복구할 수 없습니다.",
                        size=14, color=ft.Colors.BLUE_GREY_700,
                    ),
                    ft.Row([
                        ft.OutlinedButton(
                            content=ft.Text("취소"),
                            on_click=_cancel_delete,
                            expand=1,
                        ),
                        ft.ElevatedButton(
                            content=ft.Text("삭제", color=ft.Colors.WHITE),
                            bgcolor=ft.Colors.RED_700,
                            on_click=_confirm_delete,
                            expand=1,
                            height=46,
                        ),
                    ], spacing=12),
                ],
            ),
        ),
    )

    # ✅ overlay 등록 — result_sheet 포함
    page.overlay.extend([result_sheet, detail_sheet, delete_sheet])

    # ==========================================
    # 🌟 카드 클릭 시 상세보기 열기
    # ==========================================
    def _open_detail(record_id, t_name, t_date, t_time, loc,
                     m_name, w_type, results_json, sig_json, c_at):

        _current_rid["id"] = record_id

        try:
            results_dict = json.loads(results_json)
        except Exception:
            results_dict = {}

        try:
            sig_strokes = json.loads(sig_json) if sig_json else []
        except Exception:
            sig_strokes = []

        _current_rid["report_data"] = {
            "task_name":     t_name,
            "task_date":     t_date,
            "task_time":     t_time,
            "location":      loc,
            "manager_name":  m_name,
            "work_type":     w_type,
            "check_results": results_dict,
            "signature":     sig_strokes,
        }

        detail_col.controls.clear()

        # 기본정보
        detail_col.controls.append(
            ft.Text(f"📋 {t_name}", size=18, weight=ft.FontWeight.BOLD)
        )
        detail_col.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text(f"작업 종류: {w_type}", size=13, color=ft.Colors.BLUE_GREY_600),
                    ft.Text(f"작업자:   {m_name}", size=13, color=ft.Colors.BLUE_GREY_600),
                    ft.Text(f"일시:     {t_date} {t_time}", size=13, color=ft.Colors.BLUE_GREY_600),
                    ft.Text(f"장소:     {loc}", size=13, color=ft.Colors.BLUE_GREY_600),
                    ft.Text(f"저장:     {c_at}", size=12, color=ft.Colors.BLUE_GREY_400),
                ], spacing=3),
                padding=ft.Padding(12, 10, 12, 10),
                bgcolor=ft.Colors.BLUE_50,
                border_radius=8,
            )
        )

        # 체크리스트 결과
        detail_col.controls.append(
            ft.Text(f"[{w_type}] 점검 결과",
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_800,
                    size=14)
        )
        for item_text, result in results_dict.items():
            if result == "확인":
                icon_name  = ft.Icons.CHECK_CIRCLE
                icon_color = ft.Colors.GREEN_600
                text_color = ft.Colors.GREEN_800
                bg_color   = ft.Colors.GREEN_50
            else:
                icon_name  = ft.Icons.REMOVE_CIRCLE_OUTLINE
                icon_color = ft.Colors.GREY_400
                text_color = ft.Colors.GREY_600
                bg_color   = ft.Colors.GREY_50

            detail_col.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(icon_name, color=icon_color, size=16),
                        ft.Text(item_text, size=12, color=text_color, expand=True),
                        ft.Text(result, size=12, weight=ft.FontWeight.BOLD, color=icon_color),
                    ], spacing=8),
                    padding=ft.Padding(8, 6, 8, 6),
                    bgcolor=bg_color,
                    border_radius=6,
                )
            )

        # 서명 영역
        if sig_strokes:
            detail_col.controls.append(
                ft.Text("✍️ 작업자 서명",
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_800,
                        size=14)
            )
            shapes = []
            for stroke in sig_strokes:
                if len(stroke) < 2:
                    continue
                pts = [cv.Path.MoveTo(stroke[0][0], stroke[0][1])]
                for x, y in stroke[1:]:
                    pts.append(cv.Path.LineTo(x, y))
                shapes.append(cv.Path(
                    elements=pts,
                    paint=ft.Paint(
                        style=ft.PaintingStyle.STROKE,
                        color=ft.Colors.BLACK,
                        stroke_width=3,
                        stroke_cap=ft.StrokeCap.ROUND,
                        stroke_join=ft.StrokeJoin.ROUND,
                    ),
                ))
            detail_col.controls.append(
                ft.Container(
                    content=cv.Canvas(shapes=shapes, width=300, height=130),
                    bgcolor=ft.Colors.WHITE,
                    border_radius=8,
                    border=ft.Border(
                        top=ft.BorderSide(1, ft.Colors.BLACK26),
                        bottom=ft.BorderSide(1, ft.Colors.BLACK26),
                        left=ft.BorderSide(1, ft.Colors.BLACK26),
                        right=ft.BorderSide(1, ft.Colors.BLACK26),
                    ),
                )
            )

        detail_sheet.open = True
        page.update()

    # ==========================================
    # 🌟 목록 갱신
    # ==========================================
    def refresh_data():
        records = get_all_records()
        list_view.controls.clear()

        if not records:
            list_view.controls.append(
                ft.Container(
                    content=ft.Text(
                        "저장된 점검 기록이 없습니다.",
                        size=15,
                        color=ft.Colors.GREY_500,
                    ),
                    alignment=ft.Alignment(0, 0),
                    padding=ft.Padding(50, 50, 50, 50),
                )
            )
        else:
            for row in records:
                record_id          = row[0]
                task_name          = row[1]
                task_date          = row[2]
                task_time          = row[3] if len(row) > 3 else ""
                location           = row[4] if len(row) > 4 else ""
                manager_name       = row[5]
                work_type          = row[6]
                check_results_json = row[7]
                signature_json     = row[8]
                created_at         = row[9]

                def make_click(rid, tn, td, tt, loc, mn, wt, rj, sj, ca):
                    return lambda e: _open_detail(rid, tn, td, tt, loc, mn, wt, rj, sj, ca)

                list_view.controls.append(
                    ft.Card(
                        content=ft.ListTile(
                            leading=ft.Icon(
                                ft.Icons.ASSIGNMENT,
                                color=ft.Colors.BLUE_700,
                                size=30,
                            ),
                            title=ft.Text(
                                f"[{work_type}] {task_name}",
                                weight=ft.FontWeight.BOLD,
                            ),
                            subtitle=ft.Text(
                                f"작업자: {manager_name} | 일자: {task_date}\n저장: {created_at}",
                            ),
                            trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                            on_click=make_click(
                                record_id, task_name, task_date, task_time,
                                location, manager_name, work_type,
                                check_results_json, signature_json, created_at,
                            ),
                        )
                    )
                )
        page.update()

    # ==========================================
    # 🌟 화면 조립
    # ==========================================
    list_view = ft.ListView(
        expand=True, spacing=10,
        padding=ft.Padding(20, 20, 20, 20),
    )
    refresh_data()

    return ft.Column([
        ft.Container(
            content=ft.Row([
                ft.Text("과거 점검 기록", size=20, weight=ft.FontWeight.BOLD),
                ft.IconButton(
                    ft.Icons.REFRESH,
                    on_click=lambda _: refresh_data(),
                    tooltip="새로고침",
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding(left=20, top=20, right=20, bottom=10),
        ),
        list_view,
    ], expand=True)