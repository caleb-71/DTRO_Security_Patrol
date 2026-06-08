import os
import datetime
import platform  # 🌟 [신규 추가] 현재 운영체제가 윈도우인지 폰인지 확인하는 도구

def generate_html_report(data, save_path=None):
    """
    체크리스트 전체 데이터를 받아 HTML 보고서로 생성하는 함수
    (가로형 레이아웃 및 리스트 높이 조절 기능 적용)
    """
    # 1. 서명 SVG 변환
    svg_paths = ""
    if data.get("signature"):
        for stroke in data["signature"]:
            if not stroke: continue
            path_d = f"M {stroke[0][0]} {stroke[0][1]} "
            for x, y in stroke[1:]:
                path_d += f"L {x} {y} "
            svg_paths += f'<path d="{path_d}" stroke="#1e3a8a" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>\n'

    signature_svg = f'<svg width="300" height="150" viewBox="0 0 300 150" style="background-color: #f8fafc; border-radius: 8px;">{svg_paths}</svg>'

    # 2. HTML 템플릿 작성 (디자인 튜닝)
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>안전보건 점검 보고서</title>
    <style>
        body {{ font-family: 'Malgun Gothic', sans-serif; line-height: 1.6; color: #333; background-color: #f1f5f9; padding: 20px; }}
        .container {{ max-width: 800px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
        h1 {{ text-align: center; color: #1e3a8a; border-bottom: 3px solid #1e3a8a; padding-bottom: 15px; margin-bottom: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 25px; }}
        th, td {{ border: 1px solid #cbd5e1; font-size: 14px; }}
        th {{ background-color: #f8fafc; color: #0f172a; font-weight: bold; text-align: center; }}

        /* ========================================== */
        /* 🎨 상단 기본정보 표 디자인 (가로 4칸 세팅) */
        /* ========================================== */
        .info-table th {{ width: 15%; padding: 10px; }}
        .info-table td {{ width: 35%; padding: 10px; text-align: center; }}

        /* ========================================== */
        /* 🛠️ 체크리스트 표 디자인 (높이 조절 존) */
        /* ========================================== */
        .check-table th {{ padding: 12px; }}

        /* ★ 여기에 있는 padding(안쪽 여백) 숫자를 바꿔서 높이를 조절하세요! ★ 
           위아래 여백 8px, 좌우 여백 12px를 의미합니다.
           더 넓게 띄우고 싶다면 15px 12px, 꽉 차게 하고 싶다면 5px 12px로 변경해보세요. */
        .check-table td {{ 
            padding: 10px 12px; 
            height: 25px; /* 고정 높이가 필요하다면 이 숫자를 늘리거나 줄이세요 (예: 40px) */
        }}

        .status-ok {{ color: #16a34a; font-weight: bold; text-align: center; }}
        .status-ng {{ color: #dc2626; font-weight: bold; text-align: center; }}
        .item-text {{ text-align: left; }}
        .signature-box {{ text-align: right; margin-top: 30px; }}
        .signature-title {{ font-size: 16px; font-weight: bold; margin-bottom: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>[{data.get('work_type')}] 안전보건 점검 보고서</h1>

        <table class="info-table">
            <tr>
                <th>작업명</th><td>{data.get('task_name')}</td>
                <th>작업장소</th><td>{data.get('location')}</td>
            </tr>
            <tr>
                <th>작업일시</th><td>{data.get('task_date')} {data.get('task_time')}</td>
                <th>작업책임자</th><td>{data.get('manager_name')}</td>
            </tr>
        </table>

        <table class="check-table">
            <thead>
                <tr>
                    <th style="width: 75%;">점검 항목</th>
                    <th style="width: 25%;">결과</th>
                </tr>
            </thead>
            <tbody>
    """

    # 3. 체크리스트 결과 삽입
    for item, result in data.get("check_results", {}).items():
        result_class = "status-ok" if result == "확인" else "status-ng"
        html_content += f'<tr><td class="item-text">{item}</td><td class="{result_class}">{result}</td></tr>\n'

    # 4. 서명 영역 삽입 및 마무리
    html_content += f"""
            </tbody>
        </table>

        <div class="signature-box">
            <div class="signature-title">작업책임자 서명 ({data.get('manager_name')})</div>
            {signature_svg}
        </div>
    </div>
</body>
</html>
"""

    # 5. 파일 저장 로직 (PC와 스마트폰 자동 구분)
    if save_path is None:
        file_name = f"DTRO_{data.get('manager_name')}_{data.get('work_type').replace('/', '_')}.html"

        # 🌟 현재 기기가 윈도우(PC)인 경우
        if platform.system() == "Windows":
            # PC의 기본 '다운로드(Downloads)' 폴더 경로를 자동으로 찾습니다.
            save_path = os.path.join(os.path.expanduser("~"), "Downloads", file_name)
        # 🌟 안드로이드 스마트폰인 경우
        else:
            save_path = f"/storage/emulated/0/Download/{file_name}"

    try:
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return True, save_path   # ✅ 이메일 첨부를 위해 저장 경로 반환
    except Exception as e:
        return False, str(e)