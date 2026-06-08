import flet as ft
from database.db_manager import (
    delete_all_records,
    save_email_settings,
    get_email_settings,
)
from utils.email_sender import send_report_email


def SettingsView(page: ft.Page):

    # ==========================================
    # 🌟 1. 데이터 초기화 BottomSheet
    # ==========================================
    def _cancel_reset(e):
        reset_sheet.open = False
        page.update()

    def _confirm_reset(e):
        reset_sheet.open = False
        try:
            delete_all_records()
            page.snack_bar = ft.SnackBar(
                ft.Text("모든 점검 데이터가 초기화되었습니다."),
                bgcolor=ft.Colors.RED_700,
            )
        except Exception as ex:
            page.snack_bar = ft.SnackBar(
                ft.Text(f"초기화 실패: {ex}"),
                bgcolor=ft.Colors.RED_ACCENT,
            )
        page.snack_bar.open = True
        page.update()

    reset_sheet = ft.BottomSheet(
        open=False,
        content=ft.Container(
            padding=ft.Padding(24, 24, 24, 36),
            content=ft.Column(
                tight=True, spacing=16,
                controls=[
                    ft.Row([
                        ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED,
                                color=ft.Colors.RED_600, size=24),
                        ft.Text("데이터 초기화 경고", size=18,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.RED_600),
                    ], spacing=8),
                    ft.Text(
                        "정말로 모든 점검 기록을 영구 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다!",
                        size=14, color=ft.Colors.BLUE_GREY_700,
                    ),
                    ft.Row([
                        ft.OutlinedButton(
                            content=ft.Text("취소"),
                            on_click=_cancel_reset, expand=1,
                        ),
                        ft.ElevatedButton(
                            content=ft.Text("전체 삭제", color=ft.Colors.WHITE),
                            bgcolor=ft.Colors.RED_700,
                            on_click=_confirm_reset, expand=1, height=46,
                        ),
                    ], spacing=12),
                ],
            ),
        ),
    )

    # ==========================================
    # 🌟 2. 이메일 설정 BottomSheet
    # ==========================================

    # DB에서 기존 설정값 불러오기
    saved = get_email_settings()

    sender_field = ft.TextField(
        label="발신 Gmail 계정",
        hint_text="예) dtro.safety@gmail.com",
        value=saved.get("email_sender", ""),
        height=52, border_radius=10,
        keyboard_type=ft.KeyboardType.EMAIL,
        border_color=ft.Colors.BLACK26,
        text_size=14,
    )
    password_field = ft.TextField(
        label="Gmail 앱 비밀번호",
        hint_text="공백 제거 후 붙여넣기",
        value=saved.get("email_password", ""),
        password=True,          # 입력값 숨김
        can_reveal_password=True,
        height=52, border_radius=10,
        border_color=ft.Colors.BLACK26,
        text_size=14,
    )
    receiver_field = ft.TextField(
        label="수신 이메일 (관리자)",
        hint_text="예) manager@dtro.co.kr",
        value=saved.get("email_receiver", ""),
        height=52, border_radius=10,
        keyboard_type=ft.KeyboardType.EMAIL,
        border_color=ft.Colors.BLACK26,
        text_size=14,
    )

    email_status = ft.Text("", size=12, color=ft.Colors.GREEN_700)

    def _save_email_config(e):
        """이메일 설정 저장"""
        s = sender_field.value.strip()
        p = password_field.value.strip()
        r = receiver_field.value.strip()

        if not s or not p or not r:
            email_status.value = "⚠️ 모든 항목을 입력하세요."
            email_status.color = ft.Colors.RED_600
            email_status.update()
            return

        ok, msg = save_email_settings(s, p, r)
        if ok:
            email_status.value = "✅ 설정이 저장되었습니다."
            email_status.color = ft.Colors.GREEN_700
        else:
            email_status.value = f"❌ 저장 실패: {msg}"
            email_status.color = ft.Colors.RED_600
        email_status.update()

    def _test_email(e):
        """테스트 메일 전송"""
        _save_email_config(None)   # 먼저 저장

        test_data = {
            "task_name":    "테스트 발송",
            "work_type":    "이메일 설정 테스트",
            "manager_name": "관리자",
            "task_date":    "테스트",
            "location":     "",
            "task_time":    "",
            "check_results": {},
            "signature":    [],
        }

        email_status.value = "📨 테스트 메일 전송 중..."
        email_status.color = ft.Colors.BLUE_600
        email_status.update()

        # HTML 파일 없이 텍스트만 전송하는 간이 테스트
        import smtplib
        from email.mime.text import MIMEText
        from database.db_manager import get_email_settings

        cfg = get_email_settings()
        sender   = cfg.get("email_sender", "")
        password = cfg.get("email_password", "")
        receiver = cfg.get("email_receiver", "")

        if not sender or not password or not receiver:
            email_status.value = "⚠️ 설정을 먼저 저장하세요."
            email_status.color = ft.Colors.RED_600
            email_status.update()
            return

        try:
            msg = MIMEText(
                "DTRO 안전보건 앱 이메일 설정 테스트입니다.\n설정이 정상적으로 완료되었습니다.",
                "plain", "utf-8"
            )
            msg["From"]    = sender
            msg["To"]      = receiver
            msg["Subject"] = "[DTRO 안전보건] 이메일 설정 테스트"

            # 포트 587(STARTTLS) 우선 → 실패 시 465(SSL) 자동 재시도
            last_error = ""
            sent = False
            for port, use_ssl in [(587, False), (465, True)]:
                try:
                    if use_ssl:
                        conn = smtplib.SMTP_SSL("smtp.gmail.com", port, timeout=15)
                    else:
                        conn = smtplib.SMTP("smtp.gmail.com", port, timeout=15)
                        conn.ehlo()
                        conn.starttls()
                        conn.ehlo()
                    with conn as smtp:
                        smtp.login(sender, password)
                        smtp.send_message(msg)
                    sent = True
                    break
                except smtplib.SMTPAuthenticationError:
                    raise
                except Exception as ex:
                    last_error = str(ex)
                    continue

            if sent:
                email_status.value = f"✅ 테스트 메일 전송 성공!\n→ {receiver}"
                email_status.color = ft.Colors.GREEN_700
            else:
                email_status.value = f"❌ 전송 실패:\n{last_error}"
                email_status.color = ft.Colors.RED_600

        except smtplib.SMTPAuthenticationError:
            email_status.value = "❌ 인증 실패 — 앱 비밀번호를 확인하세요."
            email_status.color = ft.Colors.RED_600
        except Exception as ex:
            email_status.value = f"❌ 전송 실패: {ex}"
            email_status.color = ft.Colors.RED_600
        email_status.update()

    def _close_email_sheet(e):
        email_sheet.open = False
        page.update()

    email_sheet = ft.BottomSheet(
        open=False,
        content=ft.Container(
            padding=ft.Padding(20, 20, 20, 30),
            content=ft.Column(
                tight=True, spacing=12,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    # 헤더
                    ft.Row([
                        ft.Icon(ft.Icons.EMAIL, color=ft.Colors.BLUE_800),
                        ft.Text("이메일 발송 설정", size=17,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.BLUE_800),
                        ft.Container(expand=True),
                        ft.TextButton("닫기", on_click=_close_email_sheet),
                    ]),
                    ft.Divider(height=4),

                    # Gmail 앱 비밀번호 안내
                    ft.Container(
                        content=ft.Column([
                            ft.Text("📌 Gmail 앱 비밀번호 발급 방법",
                                    size=13, weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.BLUE_700),
                            ft.Text(
                                "① Google 계정 → 보안\n"
                                "② 2단계 인증 켜기\n"
                                "③ 앱 비밀번호 → 앱 이름 입력\n"
                                "④ 발급된 비밀번호 (공백 제거 후) 입력",
                                size=12, color=ft.Colors.BLUE_GREY_600,
                            ),
                        ], spacing=4),
                        padding=ft.Padding(12, 10, 12, 10),
                        bgcolor=ft.Colors.BLUE_50,
                        border_radius=8,
                    ),

                    sender_field,
                    password_field,
                    receiver_field,
                    email_status,

                    # 저장 / 테스트 버튼
                    ft.Row([
                        ft.OutlinedButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.SEND, size=15),
                                ft.Text("테스트 전송"),
                            ], spacing=4, tight=True),
                            on_click=_test_email,
                            expand=1,
                        ),
                        ft.ElevatedButton(
                            content=ft.Text("저장", color=ft.Colors.WHITE,
                                            weight=ft.FontWeight.BOLD),
                            bgcolor=ft.Colors.BLUE_800,
                            on_click=_save_email_config,
                            expand=1, height=46,
                        ),
                    ], spacing=10),
                ],
            ),
        ),
    )

    # ==========================================
    # 🌟 3. overlay 등록
    # ==========================================
    page.overlay.extend([reset_sheet, email_sheet])

    def open_reset_sheet(e):
        reset_sheet.open = True
        page.update()

    def open_email_sheet(e):
        # 열 때마다 DB에서 최신 설정 불러오기
        latest = get_email_settings()
        sender_field.value   = latest.get("email_sender", "")
        password_field.value = latest.get("email_password", "")
        receiver_field.value = latest.get("email_receiver", "")
        email_status.value   = ""
        email_sheet.open = True
        page.update()

    # ==========================================
    # 🌟 4. 테마 설정
    # ==========================================
    async def theme_changed(e):
        is_dark = e.control.value
        page.theme_mode = ft.ThemeMode.DARK if is_dark else ft.ThemeMode.LIGHT
        for s in page.services:
            if isinstance(s, ft.SharedPreferences):
                await s.set("theme", "dark" if is_dark else "light")
                break
        page.update()

    current_is_dark = (page.theme_mode == ft.ThemeMode.DARK)
    theme_switch = ft.Switch(
        value=current_is_dark,
        on_change=theme_changed,
        active_color=ft.Colors.BLUE_500,
    )

    # ==========================================
    # 🌟 5. UI 화면 조립
    # ==========================================
    return ft.Column([
        ft.Container(
            content=ft.Text("환경 설정", size=20, weight=ft.FontWeight.BOLD),
            padding=ft.Padding(20, 20, 0, 10),
        ),
        ft.Container(
            expand=True,
            padding=ft.Padding(10, 0, 10, 0),
            content=ft.ListView(
                spacing=5,
                controls=[
                    # 다크 모드
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.DARK_MODE,
                                        color=ft.Colors.BLUE_GREY_500),
                        title=ft.Text("어두운 배경 (다크 모드)",
                                      weight=ft.FontWeight.BOLD, size=15),
                        subtitle=ft.Text("화면 테마를 밝게 하거나 어둡게 전환합니다.",
                                         size=13),
                        trailing=theme_switch,
                        toggle_inputs=True,
                    ),
                    ft.Divider(height=20, color=ft.Colors.BLACK12),

                    # ✅ 이메일 설정 (신규)
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.EMAIL,
                                        color=ft.Colors.BLUE_600),
                        title=ft.Text("이메일 발송 설정",
                                      weight=ft.FontWeight.BOLD, size=15),
                        subtitle=ft.Text(
                            "보고서를 관리자 이메일로 자동 전송합니다.\nGmail 앱 비밀번호가 필요합니다.",
                            size=13,
                        ),
                        trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                        on_click=open_email_sheet,
                    ),
                    ft.Divider(height=20, color=ft.Colors.BLACK12),

                    # 앱 정보
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.INFO_OUTLINE,
                                        color=ft.Colors.BLUE_GREY_500),
                        title=ft.Text("앱 정보",
                                      weight=ft.FontWeight.BOLD, size=15),
                        subtitle=ft.Text("버전: 1.0.2\n개발: DTRO 안전계획팀",
                                         size=13),
                    ),
                    ft.Divider(height=20, color=ft.Colors.BLACK12),

                    # 데이터 초기화
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.WARNING_AMBER,
                                        color=ft.Colors.RED_400),
                        title=ft.Text("데이터 초기화",
                                      color=ft.Colors.RED_500,
                                      weight=ft.FontWeight.BOLD, size=15),
                        subtitle=ft.Text("모든 점검 기록과 설정을 삭제합니다.",
                                         size=13),
                        on_click=open_reset_sheet,
                    ),
                ],
            ),
        ),
    ], expand=True)