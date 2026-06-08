import os
import platform


def generate_html_report(data, save_path=None):
    """경비순찰 체크리스트 HTML 보고서 생성 (조치사항·비고 포함)"""

    # 1. 서명 SVG
    svg_paths = ""
    if data.get("signature"):
        for stroke in data["signature"]:
            if not stroke: continue
            path_d = f"M {stroke[0][0]} {stroke[0][1]} "
            for x, y in stroke[1:]:
                path_d += f"L {x} {y} "
            svg_paths += (
                f'<path d="{path_d}" stroke="#1e3a8a" stroke-width="3" '
                f'fill="none" stroke-linecap="round" stroke-linejoin="round"/>\n'
            )
    signature_svg = (
        f'<svg width="300" height="150" viewBox="0 0 300 150" '
        f'style="background-color:#f8fafc;border-radius:8px;">{svg_paths}</svg>'
    )

    # 2. HTML 생성
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>경비사 순찰 점검 보고서</title>
    <style>
        body {{ font-family: 'Malgun Gothic', sans-serif; line-height: 1.5;
               color: #333; background-color: #f1f5f9; padding: 20px; }}
        .container {{ max-width: 900px; margin: 0 auto; background: #fff;
                      padding: 30px; border-radius: 12px;
                      box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
        h1 {{ text-align: center; color: #1e3a8a;
              border-bottom: 3px solid #1e3a8a;
              padding-bottom: 12px; margin-bottom: 24px; font-size: 20px; }}
        h2 {{ text-align: center; color: #334155; font-size: 14px;
              margin-top: -16px; margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #cbd5e1; font-size: 13px; }}
        th {{ background-color: #f0f5ff; color: #1e293b;
              font-weight: bold; text-align: center; padding: 9px 6px; }}
        .info-table th {{ width: 12%; padding: 9px; }}
        .info-table td {{ padding: 9px; text-align: center; }}
        .check-table td {{ padding: 8px 10px; vertical-align: middle; }}
        .no-col   {{ width: 4%;  text-align: center; }}
        .item-col {{ width: 38%; text-align: left; }}
        .res-col  {{ width: 10%; text-align: center; }}
        .act-col  {{ width: 24%; text-align: left; }}
        .note-col {{ width: 24%; text-align: left; }}
        .status-ok {{ color: #16a34a; font-weight: bold; }}
        .status-ng {{ color: #dc2626; font-weight: bold; }}
        .status-na {{ color: #92400e; font-weight: bold; }}
        .signature-box {{ text-align: right; margin-top: 28px; }}
        .signature-title {{ font-size: 15px; font-weight: bold; margin-bottom: 8px; }}
    </style>
</head>
<body>
<div class="container">
    <h1>경비사 순찰 점검 보고서</h1>
    <h2>[{data.get('work_type')}] 순찰구역</h2>

    <table class="info-table">
        <tr>
            <th>기상상황</th><td>{data.get('location')}</td>
            <th>순찰구역</th><td>{data.get('work_type')}</td>
        </tr>
        <tr>
            <th>순찰일시</th><td>{data.get('task_date')} {data.get('task_time')}</td>
            <th>근무자</th><td>{data.get('manager_name')}</td>
        </tr>
    </table>

    <table class="check-table">
        <thead>
            <tr>
                <th class="no-col">No.</th>
                <th class="item-col">점검 항목</th>
                <th class="res-col">점검결과</th>
                <th class="act-col">조치사항</th>
                <th class="note-col">비고</th>
            </tr>
        </thead>
        <tbody>
"""
    # 3. 체크리스트 결과 (조치사항·비고 포함)
    for idx, (item, result_data) in enumerate(data.get("check_results", {}).items(), 1):
        # ✅ 구버전 호환: result_data가 문자열일 수도 있음
        if isinstance(result_data, dict):
            result = result_data.get("result", "")
            action = result_data.get("action", "")
            note   = result_data.get("note", "")
        else:
            result = str(result_data)
            action = ""
            note   = ""

        if result == "양호":
            css = "status-ok"
        elif result == "불량":
            css = "status-ng"
        else:
            css = "status-na"

        html_content += (
            f'<tr>'
            f'<td class="no-col">{idx}</td>'
            f'<td class="item-col">{item}</td>'
            f'<td class="res-col {css}">{result}</td>'
            f'<td class="act-col">{action}</td>'
            f'<td class="note-col">{note}</td>'
            f'</tr>\n'
        )

    # 4. 서명 및 마무리
    html_content += f"""
        </tbody>
    </table>

    <div class="signature-box">
        <div class="signature-title">근무자 서명 ({data.get('manager_name')})</div>
        {signature_svg}
    </div>
</div>
</body>
</html>
"""

    # 5. 저장 경로
    if save_path is None:
        fname = (
            f"DTRO_순찰_{data.get('manager_name')}_"
            f"{data.get('work_type').replace('/', '_')}.html"
        )
        if platform.system() == "Windows":
            save_path = os.path.join(os.path.expanduser("~"), "Downloads", fname)
        else:
            save_path = f"/storage/emulated/0/Download/{fname}"

    try:
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return True, save_path
    except Exception as e:
        return False, str(e)