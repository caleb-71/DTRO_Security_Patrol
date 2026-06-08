"""
utils/email_sender.py
DB에 저장된 이메일 설정을 읽어 보고서를 전송하는 모듈
- 순수 Python 표준 라이브러리만 사용 → Flet Android APK 완벽 호환
- 포트 587(STARTTLS) 우선 시도 → 실패 시 465(SSL) 자동 재시도
- 한글 파일명 RFC2231 인코딩으로 첨부파일 확장자 깨짐 방지
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from database.db_manager import get_email_settings


def send_report_email(html_path: str, data: dict) -> tuple:
    """
    DB에 저장된 이메일 설정으로 보고서를 전송합니다.
    Returns: (True, "성공 메시지") 또는 (False, "오류 메시지")
    """
    # ── DB에서 이메일 설정 읽기 ──
    settings = get_email_settings()
    sender_email    = settings.get("email_sender", "").strip()
    sender_password = settings.get("email_password", "").strip()
    receiver_email  = settings.get("email_receiver", "").strip()

    if not sender_email or not sender_password or not receiver_email:
        return False, "이메일 설정이 없습니다.\n설정 탭에서 이메일 정보를 입력해주세요."

    # ── 이메일 구성 ──
    manager_name = data.get("manager_name", "")
    work_type    = data.get("work_type", "")
    task_date    = data.get("task_date", "")
    task_name    = data.get("task_name", "")

    msg = MIMEMultipart()
    msg["From"]    = sender_email
    msg["To"]      = receiver_email
    msg["Subject"] = f"[DTRO 안전보건] {work_type} 점검보고서 — {manager_name} ({task_date})"

    body = f"""안녕하세요, DTRO 안전보건 앱에서 자동 발송된 점검 보고서입니다.

■ 작업명    : {task_name}
■ 작업 종류 : {work_type}
■ 작업자    : {manager_name}
■ 작업 일자 : {task_date}

첨부된 HTML 파일을 브라우저로 열어 점검 내역 및 서명을 확인하세요.

※ 본 메일은 DTRO 안전보건 앱에서 자동으로 발송됩니다.
"""
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # ── HTML 파일 첨부 ──
    if not os.path.exists(html_path):
        return False, f"첨부 파일을 찾을 수 없습니다:\n{html_path}"

    try:
        file_name = os.path.basename(html_path)
        with open(html_path, "rb") as f:
            file_data = f.read()

        part = MIMEBase("text", "html")               # ✅ HTML MIME 타입 명확히 지정
        part.set_payload(file_data)
        encoders.encode_base64(part)

        # ✅ RFC2231 방식으로 한글 파일명 인코딩 → .txt로 깨지는 현상 방지
        part.add_header(
            "Content-Disposition",
            "attachment",
            filename=("utf-8", "", file_name),
        )
        part.add_header("Content-Type", "text/html", name=file_name)
        msg.attach(part)

    except Exception as ex:
        return False, f"파일 첨부 실패: {ex}"

    # ── SMTP 전송: 587(STARTTLS) 우선 → 실패 시 465(SSL) 자동 재시도 ──
    last_error = ""
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
                smtp.login(sender_email, sender_password)
                smtp.send_message(msg)
            return True, f"{receiver_email} 으로 전송 완료"
        except smtplib.SMTPAuthenticationError:
            return False, "이메일 인증 실패\n앱 비밀번호를 다시 확인하세요."
        except Exception as ex:
            last_error = str(ex)
            continue

    return False, f"전송 실패 (포트 465/587 모두 차단):\n{last_error}"