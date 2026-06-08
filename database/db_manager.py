import sqlite3
import json
import os
from datetime import datetime

import platform as _platform

if _platform.system() == "Windows":
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
else:
    _BASE_DIR = os.getcwd()

DB_FILE = os.path.join(_BASE_DIR, "dtro_safety.db")


def init_db():
    """앱 최초 실행 시 DB 파일과 테이블을 생성합니다."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS checklist_records (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name     TEXT,
                task_date     TEXT,
                task_time     TEXT,
                location      TEXT,
                manager_name  TEXT,
                work_type     TEXT,
                check_results TEXT,
                signature_data TEXT,
                created_at    TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workers (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                department TEXT,
                phone      TEXT
            )
        ''')

        # ✅ 이메일 설정 테이블 추가
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        conn.commit()


# ==========================================
# 이메일 설정 저장/조회
# ==========================================
def save_email_settings(sender_email: str, sender_password: str, receiver_email: str):
    """이메일 발송 설정을 DB에 저장합니다."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            for key, value in [
                ("email_sender",   sender_email),
                ("email_password", sender_password),
                ("email_receiver", receiver_email),
            ]:
                conn.execute(
                    "INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)",
                    (key, value)
                )
            conn.commit()
        return True, "설정이 저장되었습니다."
    except sqlite3.Error as ex:
        return False, str(ex)


def get_email_settings() -> dict:
    """저장된 이메일 설정을 딕셔너리로 반환합니다."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.execute(
                "SELECT key, value FROM app_settings WHERE key IN "
                "('email_sender','email_password','email_receiver')"
            )
            rows = cursor.fetchall()
        return {row[0]: row[1] for row in rows}
    except sqlite3.Error:
        return {}


def save_checklist(task_name, task_date, task_time, location,
                   manager_name, work_type, check_results_dict, signature_strokes):
    results_json   = json.dumps(check_results_dict, ensure_ascii=False)
    signature_json = json.dumps(signature_strokes)
    current_time   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute('''
                INSERT INTO checklist_records
                (task_name, task_date, task_time, location,
                 manager_name, work_type, check_results, signature_data, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (task_name, task_date, task_time, location,
                  manager_name, work_type, results_json, signature_json, current_time))
            conn.commit()
        print(f"[{current_time}] 저장 완료 (책임자: {manager_name}, 종류: {work_type})")
    except sqlite3.Error as ex:
        print(f"[DB 오류] save_checklist: {ex}")
        raise


def get_all_records():
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.execute('SELECT * FROM checklist_records ORDER BY id DESC')
            return cursor.fetchall()
    except sqlite3.Error as ex:
        print(f"[DB 오류] get_all_records: {ex}")
        return []


def delete_record(record_id):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("DELETE FROM checklist_records WHERE id = ?", (record_id,))
            conn.commit()
    except sqlite3.Error as ex:
        print(f"[DB 오류] delete_record: {ex}")


def delete_all_records():
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("DELETE FROM checklist_records")
            conn.commit()
    except sqlite3.Error as ex:
        print(f"[DB 오류] delete_all_records: {ex}")
        raise


def add_worker(name, department, phone):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(
                "INSERT INTO workers (name, department, phone) VALUES (?, ?, ?)",
                (name, department, phone)
            )
            conn.commit()
    except sqlite3.Error as ex:
        print(f"[DB 오류] add_worker: {ex}")


def get_all_workers():
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.execute("SELECT * FROM workers ORDER BY name ASC")
            return cursor.fetchall()
    except sqlite3.Error as ex:
        print(f"[DB 오류] get_all_workers: {ex}")
        return []


def delete_worker(worker_id):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("DELETE FROM workers WHERE id = ?", (worker_id,))
            conn.commit()
    except sqlite3.Error as ex:
        print(f"[DB 오류] delete_worker: {ex}")


def get_records_by_manager(manager_name):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.execute(
                "SELECT * FROM checklist_records WHERE manager_name = ? ORDER BY id DESC",
                (manager_name,)
            )
            return cursor.fetchall()
    except sqlite3.Error as ex:
        print(f"[DB 오류] get_records_by_manager: {ex}")
        return []