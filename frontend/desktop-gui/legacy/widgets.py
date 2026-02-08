"""Reusable GUI widgets for the NPS application."""

import sys
import time
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
from gui.theme import COLORS, FONTS, CURRENCY_SYMBOLS


class ToolTip:
    """Hover tooltip for any tkinter widget.

    Shows a dark popup after a short delay (default 500ms).
    """

    def __init__(self, widget, text, delay=500):
        self._widget = widget
        self._text = text
        self._delay = delay
        self._tip_window = None
        self._after_id = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, event=None):
        self._hide()
        self._after_id = self._widget.after(self._delay, self._show)

    def _show(self):
        if self._tip_window or not self._text:
            return
        x = self._widget.winfo_rootx() + 20
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
        self._tip_window = tw = tk.Toplevel(self._widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=self._text,
            bg="#1a1a2e",
            fg="#e0e0e0",
            font=FONTS["small"],
            relief="solid",
            borderwidth=1,
            padx=8,
            pady=4,
            wraplength=300,
        )
        label.pack()

    def _hide(self, event=None):
        if self._after_id:
            self._widget.after_cancel(self._after_id)
            self._after_id = None
        if self._tip_window:
            self._tip_window.destroy()
            self._tip_window = None

    def update_text(self, text):
        self._text = text


class StyledButton(tk.Frame):
    """Cross-platform colored button (macOS ignores bg/fg on tk.Button).
    Uses a Label inside a Frame so colors work everywhere."""

    def __init__(
        self,
        parent,
        text="",
        command=None,
        bg=None,
        fg=None,
        font=None,
        padx=16,
        pady=6,
        cursor="hand2",
        state="normal",
        tooltip=None,
        **kwargs,
    ):
        bg = bg or COLORS["bg_button"]
        fg = fg or "white"
        font = font or FONTS["body"]
        super().__init__(parent, bg=bg, cursor=cursor, **kwargs)

        self._bg = bg
        self._fg = fg
        self._command = command
        self._state = state
        self._disabled_bg = COLORS["bg_input"]
        self._disabled_fg = COLORS["text_dim"]

        self._label = tk.Label(
            self,
            text=text,
            font=font,
            bg=bg,
            fg=fg,
            padx=padx,
            pady=pady,
            cursor=cursor,
        )
        self._label.pack()

        if tooltip:
            self._tooltip = ToolTip(self, tooltip)
        else:
            self._tooltip = None

        if state == "normal":
            self._label.bind("<Button-1>", self._on_click)
            self.bind("<Button-1>", self._on_click)

    def _on_click(self, event=None):
        if self._state == "disabled":
            return
        if self._command:
            self._command()

    def config(self, **kwargs):
        if "state" in kwargs:
            self._state = kwargs.pop("state")
            if self._state == "disabled":
                self.configure(bg=self._disabled_bg)
                self._label.configure(
                    bg=self._disabled_bg, fg=self._disabled_fg, cursor=""
                )
                self.configure(cursor="")
            else:
                self.configure(bg=self._bg)
                self._label.configure(bg=self._bg, fg=self._fg, cursor="hand2")
                self.configure(cursor="hand2")
        if "text" in kwargs:
            self._label.configure(text=kwargs.pop("text"))
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if kwargs:
            super().config(**kwargs)

    # Alias for ttk-style configure calls
    configure = config


def score_color(score: float) -> str:
    """Return the appropriate color hex for a harmony score."""
    if score >= 0.8:
        return COLORS["score_peak"]
    elif score >= 0.6:
        return COLORS["score_high"]
    elif score >= 0.3:
        return COLORS["score_mid"]
    else:
        return COLORS["score_low"]


def score_dots(score: float) -> str:
    """Return dot indicator for score."""
    if score >= 0.75:
        return "●●●"
    elif score >= 0.50:
        return "●●○"
    elif score >= 0.25:
        return "●○○"
    else:
        return "○○○"


class ScoreBar(tk.Canvas):
    """Horizontal bar showing 0.0 to 1.0 score with color tiers."""

    def __init__(self, parent, width=200, height=20, **kwargs):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=COLORS["bg_card"],
            highlightthickness=0,
            **kwargs,
        )
        self._width = width
        self._height = height
        self._score = 0.0

    def set_score(self, score: float):
        self._score = max(0.0, min(1.0, score))
        self.delete("all")
        # Background
        self.create_rectangle(
            0, 0, self._width, self._height, fill=COLORS["bg_input"], outline=""
        )
        # Filled portion
        fill_w = int(self._width * self._score)
        if fill_w > 0:
            color = score_color(self._score)
            self.create_rectangle(0, 0, fill_w, self._height, fill=color, outline="")
        # Score text
        self.create_text(
            self._width // 2,
            self._height // 2,
            text=f"{self._score:.2f}",
            fill=COLORS["text_bright"],
            font=FONTS["small"],
        )


class TokenDisplay(tk.Frame):
    """Shows an FC60 token with animal/element names and colored background."""

    ELEMENT_COLORS = {
        "Wood": COLORS["elem_wood"],
        "Fire": COLORS["elem_fire"],
        "Earth": COLORS["elem_earth"],
        "Metal": COLORS["elem_metal"],
        "Water": COLORS["elem_water"],
    }

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLORS["bg_card"], **kwargs)
        self.token_label = tk.Label(
            self,
            text="----",
            font=FONTS["token"],
            fg=COLORS["gold"],
            bg=COLORS["bg_card"],
        )
        self.token_label.pack()
        self.info_label = tk.Label(
            self,
            text="",
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
        )
        self.info_label.pack()

    def set_token(self, token: str, animal_name: str = "", element_name: str = ""):
        bg = self.ELEMENT_COLORS.get(element_name, COLORS["bg_card"])
        self.token_label.config(text=token, bg=bg)
        self.info_label.config(text=f"{animal_name} - {element_name}", bg=bg)
        self.config(bg=bg)


class AnimatedProgress(tk.Frame):
    """Progress bar with percentage and speed indicator."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLORS["bg"], **kwargs)
        self.canvas = tk.Canvas(self, height=24, bg=COLORS["bg"], highlightthickness=0)
        self.canvas.pack(fill="x")
        self.label = tk.Label(
            self, text="0%", font=FONTS["small"], fg=COLORS["text_dim"], bg=COLORS["bg"]
        )
        self.label.pack()
        self._progress = 0.0

    def set_progress(self, progress: float, speed_text: str = ""):
        self._progress = max(0.0, min(100.0, progress))
        self.canvas.delete("all")
        w = self.canvas.winfo_width() or 200
        h = 24
        self.canvas.create_rectangle(0, 0, w, h, fill=COLORS["bg_input"], outline="")
        fill_w = int(w * self._progress / 100.0)
        if fill_w > 0:
            self.canvas.create_rectangle(
                0, 0, fill_w, h, fill=COLORS["accent"], outline=""
            )
        text = f"{self._progress:.1f}%"
        if speed_text:
            text += f"  {speed_text}"
        self.label.config(text=text)


class StatsCard(tk.Frame):
    """Bordered card with title, big number, and subtitle."""

    def __init__(
        self, parent, title: str = "", value: str = "0", subtitle: str = "", **kwargs
    ):
        super().__init__(
            parent,
            bg=COLORS["bg_card"],
            bd=1,
            relief="solid",
            padx=12,
            pady=8,
            **kwargs,
        )
        tk.Label(
            self,
            text=title,
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
        ).pack()
        self.value_label = tk.Label(
            self,
            text=value,
            font=FONTS["stat_num"],
            fg=COLORS["text_bright"],
            bg=COLORS["bg_card"],
        )
        self.value_label.pack()
        self.subtitle_label = tk.Label(
            self,
            text=subtitle,
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
        )
        self.subtitle_label.pack()

    def set_value(self, value: str, subtitle: str = None):
        self.value_label.config(text=value)
        if subtitle is not None:
            self.subtitle_label.config(text=subtitle)


class FactorBreakdown(tk.Frame):
    """Vertical list with horizontal factor bars."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLORS["bg_card"], **kwargs)
        self._bars = {}

    def set_factors(self, factors: dict):
        """factors: {name: float 0.0-1.0}"""
        for widget in self.winfo_children():
            widget.destroy()
        self._bars = {}

        for name, value in factors.items():
            row = tk.Frame(self, bg=COLORS["bg_card"])
            row.pack(fill="x", pady=1)
            tk.Label(
                row,
                text=name,
                font=FONTS["small"],
                fg=COLORS["text_dim"],
                bg=COLORS["bg_card"],
                width=16,
                anchor="e",
            ).pack(side="left")
            canvas = tk.Canvas(
                row, width=120, height=14, bg=COLORS["bg_input"], highlightthickness=0
            )
            canvas.pack(side="left", padx=(4, 4))
            fill_w = int(120 * max(0, min(1, value)))
            if fill_w > 0:
                canvas.create_rectangle(
                    0, 0, fill_w, 14, fill=score_color(value), outline=""
                )
            tk.Label(
                row,
                text=f"{value:.2f}",
                font=FONTS["mono_sm"],
                fg=COLORS["text"],
                bg=COLORS["bg_card"],
            ).pack(side="left")
            self._bars[name] = canvas


class AIInsightPanel(tk.LabelFrame):
    """Purple-styled panel for AI insights with loading/result/error states."""

    def __init__(self, parent, title="AI Insight", **kwargs):
        super().__init__(
            parent,
            text=f"  {title}  ",
            font=FONTS["body"],
            fg=COLORS["ai_accent"],
            bg=COLORS["ai_bg"],
            bd=1,
            relief="solid",
            padx=12,
            pady=8,
            **kwargs,
        )
        self.configure(highlightbackground=COLORS["ai_border"], highlightthickness=1)

        self._text = tk.Label(
            self,
            text="",
            font=FONTS["small"],
            fg=COLORS["ai_text"],
            bg=COLORS["ai_bg"],
            wraplength=600,
            justify="left",
            anchor="nw",
        )
        self._text.pack(fill="both", expand=True)

        self._meta = tk.Label(
            self,
            text="",
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["ai_bg"],
            anchor="e",
        )
        self._meta.pack(fill="x")

    def set_loading(self, msg="Asking Claude..."):
        self._text.config(text=msg, fg=COLORS["ai_accent"])
        self._meta.config(text="")

    def set_result(self, text, elapsed=0.0, cached=False):
        self._text.config(text=text, fg=COLORS["ai_text"])
        meta = ""
        if cached:
            meta = "(cached)"
        elif elapsed > 0:
            meta = f"({elapsed:.1f}s)"
        self._meta.config(text=meta)

    def set_error(self, msg="AI analysis unavailable"):
        self._text.config(text=msg, fg=COLORS["error"])
        self._meta.config(text="")

    def set_unavailable(self):
        self._text.config(
            text="Claude CLI not available. AI features disabled.",
            fg=COLORS["text_dim"],
        )
        self._meta.config(text="")


class AIStatusIndicator(tk.Label):
    """Small AI ON/OFF indicator for the status bar."""

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            text="AI: OFF",
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
            padx=12,
            pady=4,
            **kwargs,
        )
        self.refresh()

    def refresh(self):
        try:
            from engines.ai_engine import is_available

            if is_available():
                self.config(text="AI: ON", fg=COLORS["ai_accent"])
            else:
                self.config(text="AI: OFF", fg=COLORS["text_dim"])
        except Exception:
            self.config(text="AI: OFF", fg=COLORS["text_dim"])


class LogPanel(tk.Frame):
    """Scrolled text with colored output."""

    def __init__(self, parent, height=12, **kwargs):
        super().__init__(parent, bg=COLORS["bg"], **kwargs)
        self.text = scrolledtext.ScrolledText(
            self,
            bg=COLORS["bg_card"],
            fg=COLORS["text"],
            font=FONTS["mono_sm"],
            bd=1,
            relief="solid",
            insertbackground=COLORS["text"],
            wrap="word",
            height=height,
        )
        self.text.pack(fill="both", expand=True)

        for tag, color in [
            ("info", COLORS["text"]),
            ("accent", COLORS["accent"]),
            ("success", COLORS["success"]),
            ("warning", COLORS["warning"]),
            ("error", COLORS["error"]),
            ("gold", COLORS["gold"]),
            ("purple", COLORS["purple"]),
        ]:
            self.text.tag_configure(tag, foreground=color)

    def log(self, text: str, tag: str = "info"):
        self.text.insert("end", text + "\n", tag)
        self.text.see("end")

    def clear(self):
        self.text.delete("1.0", "end")


class HighScoreAlertPanel(tk.LabelFrame):
    """Collapsible panel showing high-scoring key details with gold border."""

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            text="  High Score Alert  ",
            font=FONTS["body"],
            fg=COLORS["gold"],
            bg=COLORS["bg_card"],
            bd=1,
            relief="solid",
            padx=12,
            pady=6,
            **kwargs,
        )
        self.configure(highlightbackground=COLORS["gold"], highlightthickness=1)

        # Header row: key + score
        header = tk.Frame(self, bg=COLORS["bg_card"])
        header.pack(fill="x")

        self._key_label = tk.Label(
            header,
            text="No high-scoring keys yet",
            font=FONTS["mono_sm"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
            anchor="w",
        )
        self._key_label.pack(side="left", fill="x", expand=True)

        self._score_label = tk.Label(
            header,
            text="",
            font=FONTS["mono_sm"],
            fg=COLORS["gold"],
            bg=COLORS["bg_card"],
        )
        self._score_label.pack(side="right")

        # Detail section (toggle on click)
        self._detail_frame = tk.Frame(self, bg=COLORS["bg_card"])
        self._detail_visible = False

        # FC60 + master number
        self._fc60_label = tk.Label(
            self._detail_frame,
            text="",
            font=FONTS["mono_sm"],
            fg=COLORS["gold"],
            bg=COLORS["bg_card"],
            anchor="w",
        )
        self._fc60_label.pack(fill="x")

        # Math breakdown
        self._math_breakdown = FactorBreakdown(self._detail_frame)
        self._math_breakdown.pack(fill="x", pady=(4, 0))

        # Numerology breakdown
        self._numer_breakdown = FactorBreakdown(self._detail_frame)
        self._numer_breakdown.pack(fill="x", pady=(4, 0))

        # AI insight text
        self._ai_label = tk.Label(
            self._detail_frame,
            text="",
            font=FONTS["small"],
            fg=COLORS["ai_text"],
            bg=COLORS["bg_card"],
            wraplength=500,
            justify="left",
            anchor="nw",
        )
        self._ai_label.pack(fill="x", pady=(4, 0))

        # Click header to toggle details
        header.bind("<Button-1>", self._toggle_detail)
        self._key_label.bind("<Button-1>", self._toggle_detail)
        self._score_label.bind("<Button-1>", self._toggle_detail)

    def _toggle_detail(self, event=None):
        if self._detail_visible:
            self._detail_frame.pack_forget()
            self._detail_visible = False
        else:
            self._detail_frame.pack(fill="x", pady=(4, 0))
            self._detail_visible = True

    def show_alert(self, data):
        """Show a high-score alert. Auto-expands detail section."""
        key_hex = data.get("key", "")
        if len(key_hex) > 24:
            key_hex = key_hex[:24] + "..."
        score = data.get("score", 0)
        fc60 = data.get("fc60_token", "----")

        self._key_label.config(text=f"Key: {key_hex}", fg=COLORS["text_bright"])
        self._score_label.config(text=f"Score: {score:.3f}")
        self._fc60_label.config(text=f"FC60: {fc60}")

        math_bd = data.get("math_breakdown", {})
        numer_bd = data.get("numerology_breakdown", {})
        if math_bd:
            self._math_breakdown.set_factors(math_bd)
        if numer_bd:
            self._numer_breakdown.set_factors(numer_bd)

        self._ai_label.config(text="Waiting for AI insight...")

        # Auto-expand
        if not self._detail_visible:
            self._detail_frame.pack(fill="x", pady=(4, 0))
            self._detail_visible = True

    def set_ai_insight(self, text):
        """Update the AI insight text."""
        self._ai_label.config(text=text)


class ThrottledUpdater:
    """Rate-limits GUI updates to avoid overloading the main loop.

    Usage:
        updater = ThrottledUpdater(widget, min_interval_ms=100)
        updater.maybe_update(my_update_func, arg1, arg2)  # throttled
        updater.flush_pending()  # force any pending update
    """

    def __init__(self, widget, min_interval_ms=100):
        self._widget = widget
        self._interval = min_interval_ms / 1000.0
        self._last_update = 0.0
        self._pending = None
        self._after_id = None

    def maybe_update(self, func, *args, **kwargs):
        """Schedule func if enough time has passed, else queue it."""
        now = time.time()
        elapsed = now - self._last_update
        if elapsed >= self._interval:
            self._last_update = now
            self._cancel_pending()
            try:
                func(*args, **kwargs)
            except Exception:
                pass
        else:
            self._pending = (func, args, kwargs)
            if self._after_id is None:
                delay_ms = max(1, int((self._interval - elapsed) * 1000))
                self._after_id = self._widget.after(delay_ms, self._fire_pending)

    def flush_pending(self):
        """Force any pending update now."""
        self._cancel_pending()
        if self._pending:
            func, args, kwargs = self._pending
            self._pending = None
            self._last_update = time.time()
            try:
                func(*args, **kwargs)
            except Exception:
                pass

    def _fire_pending(self):
        self._after_id = None
        if self._pending:
            func, args, kwargs = self._pending
            self._pending = None
            self._last_update = time.time()
            try:
                func(*args, **kwargs)
            except Exception:
                pass

    def _cancel_pending(self):
        if self._after_id is not None:
            try:
                self._widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None


class LiveFeedTable(tk.Frame):
    """Scrollable live-feed table using a Treeview with color-coded rows.

    MAX_ROWS rows kept; new rows inserted at top, old trimmed from bottom.
    """

    MAX_ROWS = 200

    def __init__(self, parent, columns, col_widths=None, height=12, **kwargs):
        super().__init__(parent, bg=COLORS["bg_card"], **kwargs)

        # Configure treeview style
        style = ttk.Style()
        style.configure(
            "LiveFeed.Treeview",
            background=COLORS["bg_card"],
            foreground=COLORS["text"],
            fieldbackground=COLORS["bg_card"],
            font=FONTS["mono_sm"],
            rowheight=20,
        )
        style.configure(
            "LiveFeed.Treeview.Heading",
            background=COLORS["bg_input"],
            foreground=COLORS["text_dim"],
            font=FONTS["small"],
        )
        style.map("LiveFeed.Treeview", background=[("selected", COLORS["bg_hover"])])

        self._tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
            style="LiveFeed.Treeview",
            height=height,
        )

        for i, col in enumerate(columns):
            w = col_widths[i] if col_widths and i < len(col_widths) else 120
            self._tree.heading(col, text=col)
            self._tree.column(col, width=w, minwidth=40)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        self._tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Color tags
        self._tree.tag_configure("hit", foreground=COLORS["success"])
        self._tree.tag_configure("high_score", foreground=COLORS["gold"])
        self._tree.tag_configure("normal", foreground=COLORS["text"])
        self._tree.tag_configure("dim", foreground=COLORS["text_dim"])
        self._tree.tag_configure("error", foreground=COLORS["error"])
        self._tree.tag_configure("btc", foreground=CURRENCY_SYMBOLS["BTC"]["color"])
        self._tree.tag_configure("eth", foreground=CURRENCY_SYMBOLS["ETH"]["color"])

        self._row_count = 0

    def insert_row(self, values, tag="normal"):
        """Insert a row at the top. Trims from bottom if over MAX_ROWS."""
        self._tree.insert("", 0, values=values, tags=(tag,))
        self._row_count += 1
        if self._row_count > self.MAX_ROWS:
            children = self._tree.get_children()
            for item in children[self.MAX_ROWS :]:
                self._tree.delete(item)
            self._row_count = self.MAX_ROWS

    def clear(self):
        """Remove all rows."""
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._row_count = 0


class OracleCard(tk.LabelFrame):
    """Bordered card for displaying oracle reading sections."""

    def __init__(self, parent, title="Reading", **kwargs):
        super().__init__(
            parent,
            text=f"  {title}  ",
            font=FONTS["body"],
            fg=COLORS["oracle_accent"],
            bg=COLORS["oracle_bg"],
            bd=1,
            relief="solid",
            padx=12,
            pady=8,
            **kwargs,
        )
        self.configure(
            highlightbackground=COLORS["oracle_border"],
            highlightthickness=1,
        )
        self._sections = {}

    def add_section(self, key, label, value=""):
        """Add a labeled section to the card."""
        row = tk.Frame(self, bg=COLORS["oracle_bg"])
        row.pack(fill="x", pady=2)
        tk.Label(
            row,
            text=label,
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["oracle_bg"],
            anchor="w",
            width=16,
        ).pack(side="left")
        val_label = tk.Label(
            row,
            text=value,
            font=FONTS["mono_sm"],
            fg=COLORS["text"],
            bg=COLORS["oracle_bg"],
            anchor="w",
            wraplength=500,
            justify="left",
        )
        val_label.pack(side="left", fill="x", expand=True)
        self._sections[key] = val_label

    def set_section(self, key, value, color=None):
        """Update a section's value."""
        if key in self._sections:
            self._sections[key].config(text=value)
            if color:
                self._sections[key].config(fg=color)

    def clear_sections(self):
        """Remove all sections."""
        for widget in self.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.destroy()
        self._sections = {}


def ask_master_password(parent, first_time=False):
    """Show a modal dialog for master encryption setup.

    Returns the entered string or None if skipped.
    """
    result = {"value": None}

    dialog = tk.Toplevel(parent)
    dialog.title("NPS Security")
    dialog.geometry("400x220" if first_time else "400x180")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()

    dialog.configure(bg=COLORS["bg_card"])

    title = "Set Master Key" if first_time else "Enter Master Key"
    tk.Label(
        dialog,
        text=title,
        font=FONTS["subhead"],
        fg=COLORS["text_bright"],
        bg=COLORS["bg_card"],
    ).pack(pady=(16, 8))

    tk.Label(
        dialog,
        text="Key:",
        font=FONTS["small"],
        fg=COLORS["text_dim"],
        bg=COLORS["bg_card"],
    ).pack(anchor="w", padx=24)
    pw_entry = tk.Entry(
        dialog,
        font=FONTS["mono"],
        show="*",
        bg=COLORS["bg_input"],
        fg=COLORS["text"],
        insertbackground=COLORS["text"],
        width=30,
    )
    pw_entry.pack(padx=24, pady=(0, 4))
    pw_entry.focus_set()

    confirm_entry = None
    if first_time:
        tk.Label(
            dialog,
            text="Confirm:",
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
        ).pack(anchor="w", padx=24)
        confirm_entry = tk.Entry(
            dialog,
            font=FONTS["mono"],
            show="*",
            bg=COLORS["bg_input"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            width=30,
        )
        confirm_entry.pack(padx=24, pady=(0, 4))

    error_label = tk.Label(
        dialog,
        text="",
        font=FONTS["small"],
        fg=COLORS["error"],
        bg=COLORS["bg_card"],
    )
    error_label.pack()

    btn_frame = tk.Frame(dialog, bg=COLORS["bg_card"])
    btn_frame.pack(pady=(8, 12))

    def _on_ok():
        pw = pw_entry.get()
        if not pw:
            error_label.config(text="Entry cannot be empty")
            return
        if first_time and confirm_entry:
            if pw != confirm_entry.get():
                error_label.config(text="Entries do not match")
                return
        result["value"] = pw
        dialog.destroy()

    def _on_skip():
        dialog.destroy()

    ok_btn = tk.Button(
        btn_frame,
        text="OK",
        command=_on_ok,
        bg=COLORS["bg_success"],
        fg="white",
        font=FONTS["small"],
        padx=16,
        pady=4,
    )
    ok_btn.pack(side="left", padx=4)

    skip_btn = tk.Button(
        btn_frame,
        text="Skip (No Encryption)",
        command=_on_skip,
        bg=COLORS["bg_input"],
        fg=COLORS["text"],
        font=FONTS["small"],
        padx=16,
        pady=4,
    )
    skip_btn.pack(side="left", padx=4)

    pw_entry.bind("<Return>", lambda e: _on_ok())
    if confirm_entry:
        confirm_entry.bind("<Return>", lambda e: _on_ok())

    dialog.wait_window()
    return result["value"]


def ask_change_password(parent):
    """Show a modal dialog for changing the master encryption key.

    Returns (old_key, new_key) tuple or None if cancelled.
    """
    result = {"value": None}
    dialog = tk.Toplevel(parent)
    dialog.title("Change Master Key")
    dialog.geometry("400x260")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()
    dialog.configure(bg=COLORS["bg_card"])

    tk.Label(
        dialog,
        text="Change Master Key",
        font=FONTS["subhead"],
        fg=COLORS["text_bright"],
        bg=COLORS["bg_card"],
    ).pack(pady=(16, 8))

    fields = []
    for label_text in ["Current Key:", "New Key:", "Confirm New Key:"]:
        tk.Label(
            dialog,
            text=label_text,
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
        ).pack(anchor="w", padx=24)
        entry = tk.Entry(
            dialog,
            font=FONTS["mono"],
            show="*",
            bg=COLORS["bg_input"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            width=30,
        )
        entry.pack(padx=24, pady=(0, 4))
        fields.append(entry)

    fields[0].focus_set()
    err_lbl = tk.Label(
        dialog, text="", font=FONTS["small"], fg=COLORS["error"], bg=COLORS["bg_card"]
    )
    err_lbl.pack()
    btn_f = tk.Frame(dialog, bg=COLORS["bg_card"])
    btn_f.pack(pady=(4, 12))

    def _ok():
        old_v, new_v, cfm_v = (f.get() for f in fields)
        if not old_v:
            err_lbl.config(text="Current key is required")
            return
        if not new_v:
            err_lbl.config(text="New key is required")
            return
        if new_v != cfm_v:
            err_lbl.config(text="New keys do not match")
            return
        result["value"] = (old_v, new_v)
        dialog.destroy()

    tk.Button(
        btn_f,
        text="Change",
        command=_ok,
        bg=COLORS["bg_success"],
        fg="white",
        font=FONTS["small"],
        padx=16,
        pady=4,
    ).pack(side="left", padx=4)
    tk.Button(
        btn_f,
        text="Cancel",
        command=dialog.destroy,
        bg=COLORS["bg_input"],
        fg=COLORS["text"],
        font=FONTS["small"],
        padx=16,
        pady=4,
    ).pack(side="left", padx=4)

    fields[2].bind("<Return>", lambda e: _ok())
    dialog.wait_window()
    return result["value"]
