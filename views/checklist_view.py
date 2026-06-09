import flet as ft
import flet.canvas as cv
from datetime import datetime
from database.db_manager import save_checklist, get_all_workers
import components.styles as style
from utils.report_generator import generate_html_report
from utils.email_sender import send_report_email


def ChecklistView(page: ft.Page):

    # ==========================================
    # 🌟 1. 상태 변수
    # ==========================================
    signature_strokes = []
    current_stroke    = []

    # ==========================================
    # 🌟 2. 알림 헬퍼
    # ==========================================
    def _show_snack(msg: str, color):
        page.snack_bar = ft.SnackBar(content=ft.Text(msg), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    _r_icon  = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_700, size=30)
    _r_title = ft.Text("", size=17, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)
    _r_msg   = ft.Text("", size=13, color=style.AppColors.TEXT_MAIN)

    def _close_result(e):
        result_sheet.open = False
        page.update()

    result_sheet = ft.BottomSheet(
        open=False,
        content=ft.Container(
            padding=ft.Padding(24, 24, 24, 36),
            content=ft.Column(tight=True, spacing=16, controls=[
                ft.Row([_r_icon, _r_title], spacing=12),
                _r_msg,
                ft.ElevatedButton(
                    content=ft.Text("확인", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                    on_click=_close_result,
                    bgcolor=style.AppColors.PRIMARY,
                    height=46, width=float("inf"),
                ),
            ]),
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

    _unchecked_col = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO)

    def _close_unchecked(e):
        unchecked_sheet.open = False
        page.update()

    unchecked_sheet = ft.BottomSheet(
        open=False,
        content=ft.Container(
            padding=ft.Padding(20, 20, 20, 30),
            content=ft.Column(tight=True, spacing=12, controls=[
                ft.Row([
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED,
                            color=ft.Colors.ORANGE_700, size=22),
                    ft.Text("미체크 항목 안내", size=17, weight=ft.FontWeight.BOLD,
                            color=ft.Colors.ORANGE_700),
                ], spacing=8),
                ft.Text("아래 항목들을 양호/불량으로 선택해주세요.",
                        size=13, color=ft.Colors.BLUE_GREY_600),
                ft.Divider(height=4),
                ft.Container(content=_unchecked_col, height=280),
                ft.ElevatedButton(
                    content=ft.Text("확인", color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.ORANGE_700,
                    height=46, width=float("inf"),
                    on_click=_close_unchecked,
                ),
            ]),
        ),
    )

    def _show_unchecked(missing: list):
        _unchecked_col.controls.clear()
        for i, item in enumerate(missing, 1):
            _unchecked_col.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Text(str(i), size=11, color=ft.Colors.WHITE,
                                            weight=ft.FontWeight.BOLD,
                                            text_align=ft.TextAlign.CENTER),
                            width=22, height=22, bgcolor=ft.Colors.ORANGE_700,
                            border_radius=11, alignment=ft.Alignment(0, 0),
                        ),
                        ft.Text(item, size=13, color=ft.Colors.BLUE_GREY_800, expand=True),
                    ], spacing=10),
                    padding=ft.Padding(10, 8, 10, 8),
                    bgcolor=ft.Colors.ORANGE_50, border_radius=8,
                    border=ft.Border(
                        top=ft.BorderSide(1, ft.Colors.ORANGE_200),
                        bottom=ft.BorderSide(1, ft.Colors.ORANGE_200),
                        left=ft.BorderSide(1, ft.Colors.ORANGE_200),
                        right=ft.BorderSide(1, ft.Colors.ORANGE_200),
                    ),
                )
            )
        unchecked_sheet.open = True
        page.update()

    # ==========================================
    # 🌟 3. 서명 패드 — BottomSheet
    # ==========================================
    sign_hint = ft.Text(
        "✍️  이곳에 서명하세요",
        color=ft.Colors.BLUE_GREY_300, size=12,
        text_align=ft.TextAlign.CENTER, visible=True,
    )
    signature_canvas = cv.Canvas(shapes=[], expand=True)

    def _redraw():
        shapes = []
        for stroke in signature_strokes:
            if len(stroke) < 2: continue
            pts = [cv.Path.MoveTo(stroke[0][0], stroke[0][1])]
            for x, y in stroke[1:]:
                pts.append(cv.Path.LineTo(x, y))
            shapes.append(cv.Path(elements=pts, paint=ft.Paint(
                style=ft.PaintingStyle.STROKE, color=ft.Colors.BLACK,
                stroke_width=3, stroke_cap=ft.StrokeCap.ROUND,
                stroke_join=ft.StrokeJoin.ROUND,
            )))
        signature_canvas.shapes = shapes
        signature_canvas.update()

    def _pan_start(e: ft.DragStartEvent):
        nonlocal current_stroke
        if sign_hint.visible:
            sign_hint.visible = False; sign_hint.update()
        current_stroke = [(e.local_position.x, e.local_position.y)]
        signature_strokes.append(current_stroke)

    def _pan_update(e: ft.DragUpdateEvent):
        current_stroke.append((e.local_position.x, e.local_position.y))
        _redraw()

    def _clear_signature(e):
        signature_strokes.clear(); current_stroke.clear()
        signature_canvas.shapes = []; signature_canvas.update()
        sign_hint.visible = True; sign_hint.update()
        _set_sign_btn_state(done=False)

    def _save_signature(e):
        if not signature_strokes:
            _show_snack("서명을 먼저 그려주세요!", ft.Colors.RED_ACCENT); return
        _set_sign_btn_state(done=True)
        sign_sheet.open = False; page.update()

    def _set_sign_btn_state(done: bool):
        if done:
            sign_text.value = "서명완료"; sign_text.color = ft.Colors.GREEN_700
            sign_icon.name  = ft.Icons.CHECK_CIRCLE; sign_icon.color = ft.Colors.GREEN_700
            sign_btn.border = ft.Border(
                top=ft.BorderSide(2, ft.Colors.GREEN_500),
                bottom=ft.BorderSide(2, ft.Colors.GREEN_500),
                left=ft.BorderSide(2, ft.Colors.GREEN_500),
                right=ft.BorderSide(2, ft.Colors.GREEN_500),
            )
            sign_btn.bgcolor = ft.Colors.GREEN_50
        else:
            sign_text.value = "서명"; sign_text.color = ft.Colors.BLUE_GREY_400
            sign_icon.name  = ft.Icons.DRAW; sign_icon.color = style.AppColors.PRIMARY
            sign_btn.border = ft.Border(
                top=ft.BorderSide(1, ft.Colors.BLACK26),
                bottom=ft.BorderSide(1, ft.Colors.BLACK26),
                left=ft.BorderSide(1, ft.Colors.BLACK26),
                right=ft.BorderSide(1, ft.Colors.BLACK26),
            )
            sign_btn.bgcolor = None
        sign_btn.update()

    sign_sheet = ft.BottomSheet(
        open=False,
        content=ft.Container(
            padding=ft.Padding(20, 16, 20, 30),
            content=ft.Column(tight=True, spacing=10, controls=[
                ft.Row([
                    ft.Icon(ft.Icons.DRAW, color=style.AppColors.PRIMARY),
                    ft.Text("근무자 서명", size=17, weight=ft.FontWeight.BOLD,
                            color=style.AppColors.PRIMARY),
                ], spacing=8),
                ft.Divider(height=2),
                sign_hint,
                ft.GestureDetector(
                    on_pan_start=_pan_start, on_pan_update=_pan_update, drag_interval=8,
                    content=ft.Container(
                        width=float("inf"), height=210, bgcolor=ft.Colors.WHITE,
                        border_radius=10,
                        border=ft.Border(
                            top=ft.BorderSide(2, style.AppColors.PRIMARY),
                            bottom=ft.BorderSide(2, style.AppColors.PRIMARY),
                            left=ft.BorderSide(2, style.AppColors.PRIMARY),
                            right=ft.BorderSide(2, style.AppColors.PRIMARY),
                        ),
                        content=signature_canvas,
                    ),
                ),
                ft.Row([
                    ft.OutlinedButton(
                        content=ft.Row([ft.Icon(ft.Icons.REFRESH, size=16), ft.Text("지우기")],
                                       spacing=4, tight=True),
                        on_click=_clear_signature,
                        style=ft.ButtonStyle(side=ft.BorderSide(1, ft.Colors.RED_300),
                                              color=ft.Colors.RED_400),
                        expand=1,
                    ),
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.CHECK, size=16, color=ft.Colors.WHITE),
                            ft.Text("서명 저장", color=ft.Colors.WHITE),
                        ], spacing=4, tight=True),
                        on_click=_save_signature,
                        bgcolor=style.AppColors.PRIMARY, expand=2, height=46,
                    ),
                ], spacing=10),
            ]),
        ),
    )

    # ==========================================
    # 🌟 4. 근무자 입력 — BottomSheet
    # ==========================================
    worker_name_field = ft.TextField(
        label="근무자 이름 입력",
        hint_text="이름을 입력하고 확인 버튼을 누르세요",
        height=52, border_radius=10, text_size=16,
        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
        border_color=ft.Colors.BLACK26, autofocus=True,
    )
    worker_list_col = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO)

    def _apply_worker(name: str):
        manager_text.value = name; manager_text.color = ft.Colors.BLACK
        manager_text.size  = 18;  manager_icon.visible = False
        manager_btn.data   = name; manager_btn.update()
        worker_sheet_input.open = False; page.update()

    def confirm_worker_name(e):
        name = worker_name_field.value.strip()
        if name: _apply_worker(name)

    def build_worker_list():
        worker_list_col.controls.clear()
        workers = get_all_workers()
        if not workers: return
        worker_list_col.controls.append(
            ft.Text("👥 등록된 근무자 (탭하면 바로 선택)",
                    size=12, color=style.AppColors.TEXT_SUB)
        )
        for w in workers:
            w_name, w_dept = w[1], w[2]
            def make_tap(n): return lambda _: _apply_worker(n)
            worker_list_col.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.SECURITY, color=style.AppColors.PRIMARY, size=18),
                        ft.Column([
                            ft.Text(w_name, weight=ft.FontWeight.BOLD, size=14),
                            ft.Text(f"소속: {w_dept}", size=11, color=style.AppColors.TEXT_SUB),
                        ], spacing=1),
                    ], spacing=10),
                    padding=ft.Padding(12, 10, 12, 10), border_radius=8,
                    bgcolor=ft.Colors.BLUE_GREY_50,
                    on_click=make_tap(w_name), ink=True,
                )
            )

    worker_sheet_input = ft.BottomSheet(
        open=False,
        content=ft.Container(
            padding=ft.Padding(20, 20, 20, 30),
            content=ft.Column(tight=True, spacing=10, scroll=ft.ScrollMode.AUTO, controls=[
                ft.Row([
                    ft.Icon(ft.Icons.PERSON_SEARCH, color=style.AppColors.PRIMARY),
                    ft.Text("근무자 입력", size=17, weight=ft.FontWeight.BOLD,
                            color=style.AppColors.PRIMARY),
                ], spacing=8),
                ft.Divider(height=4),
                worker_name_field,
                ft.ElevatedButton(
                    content=ft.Text("확인", color=ft.Colors.WHITE),
                    bgcolor=style.AppColors.PRIMARY,
                    height=46, width=float("inf"),
                    on_click=confirm_worker_name,
                ),
                ft.Divider(height=4),
                worker_list_col,
            ]),
        ),
    )

    # ==========================================
    # 🌟 5. 날짜 / 시간 선택
    # ==========================================
    def on_date_change(e):
        if e.control.value:
            date_text.value = e.control.value.strftime("%Y.%m.%d")
            date_text.color = ft.Colors.BLACK; date_text.size = 18
            date_icon.visible = False; date_btn.update()

    def on_time_change(e):
        if e.control.value:
            time_text.value = e.control.value.strftime("%H:%M")
            time_text.color = ft.Colors.BLACK; time_text.size = 18
            time_icon.visible = False; time_btn.update()

    date_picker = ft.DatePicker(on_change=on_date_change)
    time_picker = ft.TimePicker(on_change=on_time_change)

    # ==========================================
    # ✅ overlay 전체 등록
    # ==========================================
    page.overlay.extend([
        result_sheet, unchecked_sheet,
        sign_sheet, worker_sheet_input,
        date_picker, time_picker,
    ])

    def open_signature_pad(e):
        sign_hint.visible = not bool(signature_strokes)
        sign_sheet.open = True; page.update()

    def open_worker_input(e):
        worker_name_field.value = ""
        build_worker_list()
        worker_sheet_input.open = True; page.update()

    def open_date_picker(e): date_picker.open = True; page.update()
    def open_time_picker(e): time_picker.open = True; page.update()

    # ==========================================
    # 🌟 6. 기본정보 카드
    #   ✅ 순찰명 제거
    #   ✅ 기상상황 가로 배치 (scroll)
    # ==========================================

    # ✅ 기상상황 — 커스텀 토글 버튼 (가로 스크롤 완전 지원)
    #    RadioGroup은 내부 스크롤을 막으므로 커스텀 버튼으로 교체
    _weather_val = {"value": "맑음"}
    _weather_btns = {}

    _weather_options = [
        ("맑음", "☀  맑음",  ft.Colors.BLUE_500),
        ("우천", "🌧  우천",  ft.Colors.BLUE_700),
        ("강풍", "💨  강풍",  ft.Colors.ORANGE_600),
        ("폭설", "❄  폭설",  ft.Colors.GREY_500),
        ("기타", "기타",     ft.Colors.GREY_600),
    ]

    def _select_weather(val: str):
        _weather_val["value"] = val
        for v, btn in _weather_btns.items():
            selected = (v == val)
            btn.bgcolor = ft.Colors.BLUE_100 if selected else ft.Colors.WHITE
            btn.border = ft.Border(
                top=ft.BorderSide(2 if selected else 1,
                                  _weather_options[[x[0] for x in _weather_options].index(v)][2]),
                bottom=ft.BorderSide(2 if selected else 1,
                                     _weather_options[[x[0] for x in _weather_options].index(v)][2]),
                left=ft.BorderSide(2 if selected else 1,
                                   _weather_options[[x[0] for x in _weather_options].index(v)][2]),
                right=ft.BorderSide(2 if selected else 1,
                                    _weather_options[[x[0] for x in _weather_options].index(v)][2]),
            )
            btn.update()

    def _make_weather_btn(val: str, label: str, color):
        selected = (val == "맑음")
        btn = ft.Container(
            content=ft.Text(label, size=13, color=color, weight=ft.FontWeight.BOLD),
            padding=ft.Padding(12, 7, 12, 7),
            border_radius=20,
            bgcolor=ft.Colors.BLUE_100 if selected else ft.Colors.WHITE,
            border=ft.Border(
                top=ft.BorderSide(2 if selected else 1, color),
                bottom=ft.BorderSide(2 if selected else 1, color),
                left=ft.BorderSide(2 if selected else 1, color),
                right=ft.BorderSide(2 if selected else 1, color),
            ),
            on_click=lambda e, v=val: _select_weather(v),
            ink=True,
        )
        _weather_btns[val] = btn
        return btn

    # ✅ 가로 스크롤 Row — RadioGroup 없이 직접 배치
    weather_row = ft.Row(
        controls=[_make_weather_btn(v, l, c) for v, l, c in _weather_options],
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
    )

    _now = datetime.now()
    date_text    = ft.Text(_now.strftime("%Y.%m.%d"), size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)
    time_text    = ft.Text(_now.strftime("%H:%M"),    size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)
    manager_text = ft.Text("근무자", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_400)
    sign_text    = ft.Text("서명",   size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_400)

    date_icon    = ft.Icon(ft.Icons.CALENDAR_MONTH, size=20, color=style.AppColors.PRIMARY, visible=False)
    time_icon    = ft.Icon(ft.Icons.ACCESS_TIME,    size=20, color=style.AppColors.PRIMARY, visible=False)
    manager_icon = ft.Icon(ft.Icons.SECURITY,       size=20, color=style.AppColors.PRIMARY)
    sign_icon    = ft.Icon(ft.Icons.DRAW,           size=20, color=style.AppColors.PRIMARY)

    def create_compact_btn(icon_obj, text_obj, click_fn):
        return ft.Container(
            content=ft.Column([icon_obj, text_obj],
                               alignment=ft.MainAxisAlignment.CENTER,
                               horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                               spacing=2),
            on_click=click_fn, expand=1, height=65, ink=True, border_radius=8,
            border=ft.Border(
                top=ft.BorderSide(1, ft.Colors.BLACK26), bottom=ft.BorderSide(1, ft.Colors.BLACK26),
                left=ft.BorderSide(1, ft.Colors.BLACK26), right=ft.BorderSide(1, ft.Colors.BLACK26),
            ),
        )

    date_btn    = create_compact_btn(date_icon,    date_text,    open_date_picker)
    time_btn    = create_compact_btn(time_icon,    time_text,    open_time_picker)
    manager_btn = create_compact_btn(manager_icon, manager_text, open_worker_input)
    manager_btn.data = ""
    sign_btn    = create_compact_btn(sign_icon, sign_text, open_signature_pad)

    custom_card_style = style.card_style()
    custom_card_style["margin"] = ft.Margin(0, 0, 0, 0)

    info_card = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.SHIELD_OUTLINED, color=style.AppColors.PRIMARY, size=20),
                ft.Text("경비순찰 기본정보", size=16, weight=ft.FontWeight.BOLD,
                        color=style.AppColors.PRIMARY),
            ]),
            # ✅ 순찰명 제거 — 날짜/시간/근무자/서명 버튼만
            ft.Row([date_btn, time_btn, manager_btn, sign_btn], spacing=8),
            # ✅ 기상상황 — 가로 1줄
            ft.Container(
                content=ft.Column([
                    ft.Text("기상상황", size=12, color=style.AppColors.TEXT_SUB,
                            weight=ft.FontWeight.BOLD),
                    weather_row,    # ✅ 가로 스크롤 토글 버튼
                ], spacing=6),
                padding=ft.Padding(8, 8, 8, 8),
                bgcolor=ft.Colors.BLUE_GREY_50,
                border_radius=8,
            ),
        ], spacing=10),
        **custom_card_style,
    )

    # ==========================================
    # 🌟 7. 체크리스트 데이터 (PDF 기반)
    # ==========================================
    work_types_list = ["관리동", "유치선/외곽울타리", "출고검사장/창고/배수로"]
    controls_dict_map = {k: {} for k in work_types_list}
    active_tab = {"work_type": work_types_list[0]}

    patrol_data = {
        "관리동": {
            "has_na": False,
            "items": [
                "‣ 화재·연기·타는 냄새·불꽃 등 이상징후 여부",
                "‣ 유류·위험물·인화성 물질 관리상태 이상 여부",
                "‣ 전기장판·전자레인지 등 미사용 전기제품 전원 차단 여부",
                "‣ 사무실·휴게실 형광등 및 전원 OFF 상태 확인",
                "‣ 조명 점등 상태 정상 여부",
                "‣ 출입문·잠금장치·시건장치 이상 여부",
                "‣ 무단침입 및 수상자 배회 여부",
                "‣ 절도·파손 흔적 여부",
                "‣ 기타 특이사항 확인",
            ],
        },
        "유치선/외곽울타리": {
            "has_na": True,
            "items": [
                "‣ 시설물 및 구조물(외곽 울타리·펜스) 파손 여부",
                "‣ 무단침입 및 수상자 배회 여부",
                "‣ 절도·파손 흔적 여부",
                "‣ 경보기·보안시스템·CCTV 정상 작동 여부",
                "‣ 불법촬영·드론 비행 여부",
                "‣ 테러·방화 의심 물품 존재 여부",
                "‣ 유치선 이상 여부",
                "‣ 기타 특이사항 확인",
            ],
        },
        "출고검사장/창고/배수로": {
            "has_na": True,
            "items": [
                "‣ 화재·연기·타는 냄새·불꽃 등 이상징후 여부",
                "‣ 유류·위험물·인화성 물질 관리상태 이상 여부",
                "‣ 건축물 균열·침하·누수·침수 등 이상 여부",
                "‣ 제설·배수로·배수시설 이상 여부",
                "‣ 조명 점등 상태 정상 여부",
                "‣ 무단침입 및 수상자 배회 여부",
                "‣ 출입문·잠금장치·시건장치 이상 여부",
                "‣ 테러·방화 의심 물품 존재 여부",
                "‣ 강풍·폭우·폭설 등 기상이변 위험요인 여부",
                "‣ 검사장 이상 여부",
                "‣ 기타 특이사항 확인",
            ],
        },
    }

    def make_check_item(text, work_type, has_na=False):
        """
        ✅ 각 항목마다 조치사항·비고 입력 필드 추가
        """
        radios = [
            ft.Radio(value="양호", label="양호", fill_color=ft.Colors.TEAL_600),
            ft.Radio(value="불량", label="불량", fill_color=ft.Colors.RED_600),
        ]
        if has_na:
            radios.append(
                ft.Radio(value="해당없음", label="해당없음", fill_color=ft.Colors.AMBER_700)
            )
        rg = ft.RadioGroup(content=ft.Row(radios, spacing=16))

        # ✅ 조치사항 / 비고 텍스트 입력 필드
        action_field = ft.TextField(
            label="조치사항",
            height=44, expand=True, border_radius=8, text_size=12,
            content_padding=ft.Padding(8, 4, 8, 4),
            border_color=ft.Colors.BLACK26,
        )
        note_field = ft.TextField(
            label="비고",
            height=44, expand=True, border_radius=8, text_size=12,
            content_padding=ft.Padding(8, 4, 8, 4),
            border_color=ft.Colors.BLACK26,
        )

        # ✅ controls_dict_map에 rg + action + note 함께 저장
        controls_dict_map[work_type][text] = {
            "rg":     rg,
            "action": action_field,
            "note":   note_field,
        }

        return ft.Container(
            content=ft.Column([
                ft.Text(text, weight=ft.FontWeight.W_600, color=style.AppColors.TEXT_MAIN),
                rg,
                ft.Row([action_field, note_field], spacing=8),
            ], spacing=6),
            padding=14, bgcolor=ft.Colors.BLUE_GREY_50, border_radius=12,
        )

    # ==========================================
    # 🌟 8. DB 저장
    # ==========================================
    def on_save_click(e):
        if not manager_btn.data:
            _show_snack("근무자를 입력하세요.", ft.Colors.RED_ACCENT); return
        if not signature_strokes:
            _show_snack("근무자 서명이 누락되었습니다!", ft.Colors.RED_ACCENT); return

        current_work = active_tab["work_type"]
        # ✅ missing 체크: controls_dict_map 구조 변경 반영
        missing = [t for t, v in controls_dict_map[current_work].items() if not v["rg"].value]
        if missing:
            _show_unchecked(missing); return

        # ✅ results에 result + action + note 포함
        results = {
            t: {
                "result": v["rg"].value,
                "action": v["action"].value.strip(),
                "note":   v["note"].value.strip(),
            }
            for t, v in controls_dict_map[current_work].items()
        }
        try:
            save_checklist(
                current_work,               # task_name = 순찰구역
                date_text.value,
                time_text.value,
                _weather_val["value"] or "맑음",  # location = 기상상황
                manager_btn.data,
                current_work,
                results,
                signature_strokes,
            )
            _show_result(
                title="순찰기록 저장 완료",
                msg=f"[{current_work}] 순찰 점검 기록이\nDB에 저장되었습니다.",
                success=True,
            )
        except Exception as ex:
            _show_result(title="저장 오류", msg=f"저장 중 문제 발생:\n{ex}", success=False)

    # ==========================================
    # 🌟 9. HTML 보고서 발행 + 이메일 전송
    # ==========================================
    def on_html_report_click(e):
        if not manager_btn.data:
            _show_snack("근무자를 입력하세요.", ft.Colors.RED_ACCENT); return
        if not signature_strokes:
            _show_snack("근무자 서명이 누락되었습니다!", ft.Colors.RED_ACCENT); return

        current_work = active_tab["work_type"]
        missing = [t for t, v in controls_dict_map[current_work].items() if not v["rg"].value]
        if missing:
            _show_unchecked(missing); return

        data = {
            "task_name":     current_work,
            "task_date":     date_text.value,
            "task_time":     time_text.value,
            "location":      _weather_val["value"] or "맑음",
            "manager_name":  manager_btn.data,
            "work_type":     current_work,
            "check_results": {
                t: {
                    "result": v["rg"].value,
                    "action": v["action"].value.strip(),
                    "note":   v["note"].value.strip(),
                }
                for t, v in controls_dict_map[current_work].items()
            },
            "signature": signature_strokes,
        }
        try:
            ok, result = generate_html_report(data)
            if not ok:
                _show_result(title="발행 실패", msg=f"보고서 생성 실패:\n{result}", success=False)
                return
            html_path = result
            email_ok, email_msg = send_report_email(html_path, data)
            if email_ok:
                _show_result(
                    title="발행 및 전송 완료",
                    msg="순찰 보고서가 저장되고\n관리자 이메일로 전송되었습니다.",
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

    # ==========================================
    # 🌟 10. 체크리스트 탭 구성
    # ==========================================
    def create_tab_content(work_type):
        info   = patrol_data[work_type]
        has_na = info["has_na"]
        items  = info["items"]

        section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.FACT_CHECK, color=style.AppColors.PRIMARY),
                    ft.Text(f"{work_type} 순찰 점검", size=17,
                            weight=ft.FontWeight.BOLD, color=style.AppColors.PRIMARY),
                    ft.Container(expand=True),
                    ft.Container(
                        content=ft.Text(
                            "양호/불량/해당없음" if has_na else "양호/불량",
                            size=11, color=style.AppColors.TEXT_SUB,
                        ),
                        padding=ft.Padding(6, 3, 6, 3),
                        bgcolor=ft.Colors.BLUE_GREY_50, border_radius=6,
                    ),
                ]),
                *[make_check_item(item, work_type, has_na=has_na) for item in items],
            ], spacing=10),
            **style.card_style(),
        )

        save_btn = ft.Container(
            content=ft.ElevatedButton(
                content=ft.Text("순찰기록 DB 저장", color=style.AppColors.WHITE),
                on_click=on_save_click, icon=ft.Icons.SAVE,
                style=ft.ButtonStyle(bgcolor=ft.Colors.TRANSPARENT,
                                     shadow_color=ft.Colors.TRANSPARENT),
                width=float("inf"), height=55,
            ),
            gradient=style.SAVE_BUTTON_GRADIENT, border_radius=12,
            shadow=style.COMMON_SHADOW,
            margin=ft.Margin(left=0, top=10, right=0, bottom=0),
        )
        html_btn = ft.Container(
            content=ft.ElevatedButton(
                content=ft.Text("보고서 발행 (HTML)", color=style.AppColors.WHITE),
                on_click=on_html_report_click, icon=ft.Icons.WEB,
                style=ft.ButtonStyle(bgcolor=ft.Colors.TRANSPARENT,
                                     shadow_color=ft.Colors.TRANSPARENT),
                width=float("inf"), height=55,
            ),
            gradient=style.PDF_BUTTON_GRADIENT, border_radius=12,
            shadow=style.COMMON_SHADOW,
            margin=ft.Margin(left=0, top=0, right=0, bottom=20),
        )
        return ft.ListView(
            expand=True, spacing=10, padding=20,
            controls=[section, save_btn, html_btn],
        )

    tab_content_view = ft.Container(expand=True, content=create_tab_content(work_types_list[0]))

    def on_tab_change(e):
        sel = e.control.data
        active_tab["work_type"] = sel
        for c in tab_row.controls:
            if c.data == sel:
                c.border         = ft.Border(bottom=ft.BorderSide(3, style.AppColors.PRIMARY))
                c.content.color  = style.AppColors.PRIMARY
                c.content.weight = ft.FontWeight.BOLD
            else:
                c.border         = None
                c.content.color  = style.AppColors.TEXT_SUB
                c.content.weight = ft.FontWeight.NORMAL
        tab_content_view.content = create_tab_content(sel)
        tab_row.update(); tab_content_view.update()

    tab_row = ft.Row(
        scroll=ft.ScrollMode.AUTO, spacing=0,
        controls=[
            ft.Container(
                data=wt,
                content=ft.Text(
                    wt, size=14,
                    weight=ft.FontWeight.BOLD if wt == work_types_list[0] else ft.FontWeight.NORMAL,
                    color=style.AppColors.PRIMARY if wt == work_types_list[0] else style.AppColors.TEXT_SUB,
                ),
                padding=ft.Padding(14, 12, 14, 12),
                border=ft.Border(bottom=ft.BorderSide(3, style.AppColors.PRIMARY)) if wt == work_types_list[0] else None,
                on_click=on_tab_change, ink=True,
            )
            for wt in work_types_list
        ],
    )

    tabs_container = ft.Column([
        ft.Container(content=tab_row, bgcolor=ft.Colors.WHITE, shadow=style.COMMON_SHADOW),
        tab_content_view,
    ], expand=True, spacing=0)

    return ft.Column([
        ft.Container(content=info_card, padding=ft.Padding(left=15, top=5, right=15, bottom=0)),
        ft.Container(content=tabs_container, expand=True,
                     margin=ft.Margin(left=0, top=-5, right=0, bottom=0)),
    ], expand=True, spacing=0)