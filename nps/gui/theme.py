"""Color palette, fonts, and shared styles for the NPS GUI."""

import sys

COLORS = {
    # Base
    "bg": "#0d1117",
    "bg_card": "#161b22",
    "bg_input": "#21262d",
    "bg_hover": "#1c2128",
    "bg_button": "#1f6feb",
    "bg_danger": "#da3633",
    "bg_success": "#238636",
    "border": "#30363d",
    # Text
    "text": "#c9d1d9",
    "text_dim": "#8b949e",
    "text_bright": "#f0f6fc",
    # Accents
    "gold": "#d4a017",
    "gold_dim": "#a67c00",
    "accent": "#58a6ff",
    "success": "#3fb950",
    "warning": "#d29922",
    "error": "#f85149",
    "purple": "#a371f7",
    # Score colors
    "score_low": "#f85149",
    "score_mid": "#d29922",
    "score_high": "#238636",
    "score_peak": "#d4a017",
    # AI colors
    "ai_bg": "#1a1033",
    "ai_border": "#7c3aed",
    "ai_text": "#c4b5fd",
    "ai_accent": "#a78bfa",
    # Element colors
    "elem_wood": "#2d5016",
    "elem_fire": "#8b1a1a",
    "elem_earth": "#6b4226",
    "elem_metal": "#4a4a4a",
    "elem_water": "#1a3a5c",
    # Oracle colors
    "oracle_bg": "#0f1a2e",
    "oracle_border": "#1e3a5f",
    "oracle_accent": "#4fc3f7",
}

FONTS = {
    "heading": ("Segoe UI", 16, "bold"),
    "subhead": ("Segoe UI", 12, "bold"),
    "body": ("Segoe UI", 10),
    "small": ("Segoe UI", 9),
    "mono": ("Consolas", 10),
    "mono_lg": ("Consolas", 12),
    "mono_sm": ("Consolas", 9),
    "score": ("Consolas", 18, "bold"),
    "token": ("Consolas", 14, "bold"),
    "stat_num": ("Consolas", 18, "bold"),
    "tab_title": ("Segoe UI", 11, "bold"),
}

CURRENCY_SYMBOLS = {
    "BTC": {"symbol": "₿", "color": "#F7931A"},
    "ETH": {"symbol": "Ξ", "color": "#627EEA"},
    "USDT": {"symbol": "₮", "color": "#26A17B"},
    "USDC": {"symbol": "◉", "color": "#2775CA"},
    "DAI": {"symbol": "◈", "color": "#F5AC37"},
    "WBTC": {"symbol": "₿w", "color": "#F09242"},
    "LINK": {"symbol": "⬡", "color": "#2A5ADA"},
    "SHIB": {"symbol": "SHIB", "color": "#FFA409"},
}

# Linux/Mac font fallbacks
if sys.platform != "win32":
    for key in FONTS:
        f = list(FONTS[key])
        if f[0] == "Segoe UI":
            f[0] = "Helvetica"
        elif f[0] == "Consolas":
            f[0] = "Courier"
        FONTS[key] = tuple(f)
