import smtplib
import flet as ft
from email.mime.text import MIMEText

from database.db_manager import (
    delete_all_records,
    save_email_settings,
    get_email_settings,
)
from utils.email_sender import _get_smtp_server


def SettingsView(page: ft.Page):

    # ==========================================
    # 1. 데이터 초기화 BottomSheet
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
                        "정말로 모든 점검 기록을 영구 삭제하시겠습니까?\n"
                        "이 작업은 되돌릴 수 없습니다!",
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
    # 2. 이메일 설정 BottomSheet
    # ==========================================
    saved = get_email_settings()

    sender_field = ft.TextField(
        label="발신 이메일 계정",
        hint_text="예) dtro@gmail.com  또는  dtro@naver.com",
        value=saved.get("email_sender", ""),
        height=52, border_radius=10,
        keyboard_type=ft.KeyboardType.EMAIL,
        border_color=ft.Colors.BLACK26,
        text_size=14,
    )
    password_field = ft.TextField(
        label="비밀번호 / 앱 비밀번호",
        hint_text="Gmail: 16자리 앱 비밀번호 / 네이버: 12자리 애플리케이션 비밀번호",
        value=saved.get("email_password", ""),
        password=True,
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
        s = sender_field.value.strip()
        p = password_field.value.strip()
        r = receiver_field.value.strip()
        if not s or not p or not r:
            email_status.value = "모든 항목을 입력하세요."
            email_status.color = ft.Colors.RED_600
            email_status.update()
            return
        ok, msg = save_email_settings(s, p, r)
        if ok:
            email_status.value = "설정이 저장되었습니다."
            email_status.color = ft.Colors.GREEN_700
        else:
            email_status.value = f"저장 실패: {msg}"
            email_status.color = ft.Colors.RED_600
        email_status.update()

    def _test_email(e):
        _save_email_config(None)
        cfg      = get_email_settings()
        sender   = cfg.get("email_sender",   "").strip()
        password = cfg.get("email_password", "").strip()
        receiver = cfg.get("email_receiver", "").strip()
        if not sender or not password or not receiver:
            email_status.value = "설정을 먼저 저장하세요."
            email_status.color = ft.Colors.RED_600
            email_status.update()
            return

        email_status.value = "테스트 메일 전송 중..."
        email_status.color = ft.Colors.BLUE_600
        email_status.update()

        # ✅ 도메인 자동 감지 (Gmail/네이버/다음/카카오)
        smtp_server = _get_smtp_server(sender)

        try:
            msg = MIMEText(
                "DTRO 경비순찰 앱 이메일 설정 테스트입니다.\n"
                "설정이 정상적으로 완료되었습니다.",
                "plain", "utf-8",
            )
            msg["From"]    = sender
            msg["To"]      = receiver
            msg["Subject"] = "[DTRO 경비순찰] 이메일 설정 테스트"

            last_error = ""
            sent = False
            for port, use_ssl in [(587, False), (465, True)]:
                try:
                    if use_ssl:
                        conn = smtplib.SMTP_SSL(smtp_server, port, timeout=15)
                    else:
                        conn = smtplib.SMTP(smtp_server, port, timeout=15)
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
                email_status.value = f"테스트 메일 전송 성공! -> {receiver}"
                email_status.color = ft.Colors.GREEN_700
            else:
                email_status.value = f"전송 실패:\n{last_error}"
                email_status.color = ft.Colors.RED_600

        except smtplib.SMTPAuthenticationError:
            email_status.value = "인증 실패 - 비밀번호를 확인하세요."
            email_status.color = ft.Colors.RED_600
        except Exception as ex:
            email_status.value = f"전송 실패: {ex}"
            email_status.color = ft.Colors.RED_600
        email_status.update()

    def _close_email_sheet(e):
        email_sheet.open = False
        page.update()

    # ✅ Gmail 16자리 / 네이버 12자리 통합 안내
    email_guide = ft.Container(
        content=ft.Column([
            ft.Text("이메일 계정별 비밀번호 안내",
                    size=13, weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_700),
            ft.Divider(height=4, color=ft.Colors.BLUE_200),
            ft.Text("Gmail - 앱 비밀번호 16자리",
                    size=12, weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_800),
            ft.Text(
                "Google 계정 -> 보안 -> 2단계 인증 켜기\n"
                "앱 비밀번호 -> 앱 이름 입력 -> [만들기]\n"
                "발급된 16자리 (공백 제거 후) 입력\n"
                "예) abcdefghijklmnop",
                size=12, color=ft.Colors.BLUE_GREY_600,
            ),
            ft.Divider(height=4, color=ft.Colors.BLUE_200),
            ft.Text("네이버 - 애플리케이션 비밀번호 12자리",
                    size=12, weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREEN_800),
            ft.Text(
                "nid.naver.com 로그인\n"
                "보안설정 -> 2단계 인증 -> [관리] 클릭\n"
                "애플리케이션 비밀번호 관리 -> [생성하기]\n"
                "종류: 직접입력 -> 앱 이름 (예: DTRO순찰)\n"
                "발급된 12자리 비밀번호 메모 후 입력\n"
                "※ 창 닫으면 다시 볼 수 없으니 반드시 메모!",
                size=12, color=ft.Colors.BLUE_GREY_600,
            ),
            ft.Divider(height=4, color=ft.Colors.BLUE_200),
            ft.Container(
                content=ft.Text(
                    "주의: 로그인 비밀번호 직접 입력 시 보안 오류 발생!\n"
                    "반드시 앱/애플리케이션 전용 비밀번호를 사용하세요.",
                    size=11, color=ft.Colors.RED_700,
                ),
                padding=ft.Padding(8, 6, 8, 6),
                bgcolor=ft.Colors.RED_50,
                border_radius=6,
            ),
        ], spacing=6),
        padding=ft.Padding(12, 10, 12, 10),
        bgcolor=ft.Colors.BLUE_50,
        border_radius=8,
    )

    email_sheet = ft.BottomSheet(
        open=False,
        content=ft.Container(
            padding=ft.Padding(20, 20, 20, 30),
            content=ft.Column(
                tight=True, spacing=12,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Row([
                        ft.Icon(ft.Icons.EMAIL, color=ft.Colors.BLUE_800),
                        ft.Text("이메일 발송 설정", size=17,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.BLUE_800),
                        ft.Container(expand=True),
                        ft.TextButton("닫기", on_click=_close_email_sheet),
                    ]),
                    ft.Divider(height=4),
                    email_guide,
                    sender_field,
                    password_field,
                    receiver_field,
                    email_status,
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
    # 3. overlay 등록
    # ==========================================
    page.overlay.extend([reset_sheet, email_sheet])

    def open_reset_sheet(e):
        reset_sheet.open = True
        page.update()

    def open_email_sheet(e):
        latest = get_email_settings()
        sender_field.value   = latest.get("email_sender",   "")
        password_field.value = latest.get("email_password", "")
        receiver_field.value = latest.get("email_receiver", "")
        email_status.value   = ""
        email_sheet.open = True
        page.update()

    # ==========================================
    # 4. 테마 설정
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
    # 5. UI 화면 조립
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
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.DARK_MODE,
                                        color=ft.Colors.BLUE_GREY_500),
                        title=ft.Text("어두운 배경 (다크 모드)",
                                      weight=ft.FontWeight.BOLD, size=15),
                        subtitle=ft.Text(
                            "화면 테마를 밝게 하거나 어둡게 전환합니다.",
                            size=13),
                        trailing=theme_switch,
                        toggle_inputs=True,
                    ),
                    ft.Divider(height=20, color=ft.Colors.BLACK12),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.EMAIL,
                                        color=ft.Colors.BLUE_600),
                        title=ft.Text("이메일 발송 설정",
                                      weight=ft.FontWeight.BOLD, size=15),
                        subtitle=ft.Text(
                            "보고서를 관리자 이메일로 자동 전송합니다.\n"
                            "Gmail, 네이버, 다음, 카카오 지원",
                            size=13,
                        ),
                        trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                        on_click=open_email_sheet,
                    ),
                    ft.Divider(height=20, color=ft.Colors.BLACK12),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.INFO_OUTLINE,
                                        color=ft.Colors.BLUE_GREY_500),
                        title=ft.Text("앱 정보",
                                      weight=ft.FontWeight.BOLD, size=15),
                        subtitle=ft.Text(
                            "버전: 1.0.0\n개발: DTRO 안전계획팀",
                            size=13),
                    ),
                    ft.Divider(height=20, color=ft.Colors.BLACK12),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.WARNING_AMBER,
                                        color=ft.Colors.RED_400),
                        title=ft.Text("데이터 초기화",
                                      color=ft.Colors.RED_500,
                                      weight=ft.FontWeight.BOLD, size=15),
                        subtitle=ft.Text(
                            "모든 점검 기록과 설정을 삭제합니다.",
                            size=13),
                        on_click=open_reset_sheet,
                    ),
                ],
            ),
        ),
    ], expand=True)