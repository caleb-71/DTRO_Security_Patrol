import flet as ft

# 🛡️ 최신 버전 호환 패치
_C = ft.Colors if hasattr(ft, 'Colors') else ft.colors
_I = ft.Icons if hasattr(ft, 'Icons') else ft.icons

class AppColors:
    PRIMARY       = _C.BLUE_800
    PRIMARY_LIGHT = _C.BLUE_50
    SECONDARY     = _C.TEAL_700
    ACCENT        = _C.DEEP_ORANGE_600
    BACKGROUND    = _C.GREY_100
    WHITE         = _C.WHITE
    TEXT_MAIN     = _C.BLUE_GREY_900
    TEXT_SUB      = _C.BLUE_GREY_400

COMMON_SHADOW = ft.BoxShadow(
    spread_radius=1,
    blur_radius=12,
    color=ft.Colors.with_opacity(0.15, _C.BLACK) if hasattr(ft, 'Colors') else ft.colors.with_opacity(0.15, _C.BLACK),
    offset=ft.Offset(0, 5)
)

SAVE_BUTTON_GRADIENT = ft.LinearGradient(
    begin=ft.Alignment(-1.0, -1.0),
    end=ft.Alignment(1.0, 1.0),
    colors=[_C.BLUE_700, _C.INDIGO_800]
)

PDF_BUTTON_GRADIENT = ft.LinearGradient(
    begin=ft.Alignment(-1.0, -1.0),
    end=ft.Alignment(1.0, 1.0),
    colors=[_C.ORANGE_700, _C.RED_700]
)

def card_style():
    return {
        "padding": 20,
        "bgcolor": AppColors.WHITE,
        "border_radius": 18,
        # ✅ 최신 버전 Flet 규격: ft.padding.only() 제거 후 ft.Margin() 사용
        "margin": ft.Margin(left=0, top=0, right=0, bottom=15),
        "shadow": COMMON_SHADOW
    }

RADIO_THEME = {
    "confirm": _C.TEAL_500,
    "none":    _C.AMBER_700
}