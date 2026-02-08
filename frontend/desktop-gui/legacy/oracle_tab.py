"""Oracle tab — multi-system sign reader + name cipher."""

import json
import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
from pathlib import Path
from gui.theme import COLORS, FONTS
from gui.widgets import StyledButton, AIInsightPanel, OracleCard


class OracleTab:
    """Sign Reader + Name Analysis tab."""

    HISTORY_FILE = Path(__file__).parent.parent / "data" / "oracle_readings.json"
    MAX_HISTORY = 100

    def __init__(self, parent, app=None):
        self.parent = parent
        self.app = app
        self._history = []
        self._load_history()
        self._build_ui()

    def _build_ui(self):
        main = tk.Frame(self.parent, bg=COLORS["bg"], padx=12, pady=8)
        main.pack(fill="both", expand=True)

        tk.Label(
            main,
            text="Oracle",
            font=FONTS["heading"],
            fg=COLORS["oracle_accent"],
            bg=COLORS["bg"],
        ).pack(anchor="w", pady=(0, 6))

        # Two-column layout
        cols = tk.Frame(main, bg=COLORS["bg"])
        cols.pack(fill="both", expand=True)

        left = tk.Frame(cols, bg=COLORS["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))

        right = tk.Frame(cols, bg=COLORS["bg"])
        right.pack(side="left", fill="both", expand=True, padx=(6, 0))

        # Left column: Sign Input + Reading Display
        self._build_sign_input(left)
        self._build_sign_display(left)

        # Right column: Name Input + Name Display + AI + History
        self._build_name_input(right)
        self._build_name_display(right)
        self._build_ai_panel(right)
        self._build_history_panel(right)

    # ─── Sign Input ───
    def _build_sign_input(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="  Sign Reader  ",
            font=FONTS["body"],
            fg=COLORS["oracle_accent"],
            bg=COLORS["bg_card"],
            bd=1,
            relief="solid",
            padx=12,
            pady=8,
        )
        frame.pack(fill="x", pady=(0, 6))

        # Sign input
        row1 = tk.Frame(frame, bg=COLORS["bg_card"])
        row1.pack(fill="x", pady=2)
        tk.Label(
            row1,
            text="Sign:",
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
            width=8,
            anchor="e",
        ).pack(side="left")
        self._sign_entry = tk.Entry(
            row1,
            font=FONTS["mono"],
            bg=COLORS["bg_input"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            width=20,
        )
        self._sign_entry.pack(side="left", padx=(4, 0))
        self._sign_entry.insert(0, "11:11")

        # Date input
        row2 = tk.Frame(frame, bg=COLORS["bg_card"])
        row2.pack(fill="x", pady=2)
        tk.Label(
            row2,
            text="Date:",
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
            width=8,
            anchor="e",
        ).pack(side="left")
        self._date_entry = tk.Entry(
            row2,
            font=FONTS["mono"],
            bg=COLORS["bg_input"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            width=12,
        )
        self._date_entry.pack(side="left", padx=(4, 0))
        self._date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # Time input
        tk.Label(
            row2,
            text="Time:",
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
        ).pack(side="left", padx=(8, 0))
        self._time_entry = tk.Entry(
            row2,
            font=FONTS["mono"],
            bg=COLORS["bg_input"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            width=8,
        )
        self._time_entry.pack(side="left", padx=(4, 0))
        self._time_entry.insert(0, datetime.now().strftime("%H:%M"))

        # Reading mode toggle
        mode_row = tk.Frame(frame, bg=COLORS["bg_card"])
        mode_row.pack(fill="x", pady=(4, 0))
        tk.Label(
            mode_row,
            text="Mode:",
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
            width=8,
            anchor="e",
        ).pack(side="left")
        self._reading_mode = tk.StringVar(value="full")
        tk.Radiobutton(
            mode_row,
            text="Full Reading",
            variable=self._reading_mode,
            value="full",
            font=FONTS["small"],
            fg=COLORS["text"],
            bg=COLORS["bg_card"],
            selectcolor=COLORS["bg_input"],
            activebackground=COLORS["bg_card"],
            activeforeground=COLORS["text"],
        ).pack(side="left", padx=(4, 8))
        tk.Radiobutton(
            mode_row,
            text="Quick Question",
            variable=self._reading_mode,
            value="question",
            font=FONTS["small"],
            fg=COLORS["text"],
            bg=COLORS["bg_card"],
            selectcolor=COLORS["bg_input"],
            activebackground=COLORS["bg_card"],
            activeforeground=COLORS["text"],
        ).pack(side="left")

        # Read button
        row3 = tk.Frame(frame, bg=COLORS["bg_card"])
        row3.pack(fill="x", pady=(6, 0))
        StyledButton(
            row3,
            text="Read Sign",
            command=self._read_sign,
            bg=COLORS["oracle_accent"],
            fg="white",
            font=FONTS["small"],
            padx=12,
            pady=4,
            tooltip="Perform a numerological reading of the sign",
        ).pack(side="left")

    # ─── Sign Display ───
    def _build_sign_display(self, parent):
        self._sign_cards = {}

        for key, title in [
            ("pythagorean", "Pythagorean"),
            ("fc60", "FC60 / Base-60"),
            ("moon", "Moon Phase"),
            ("ganzhi", "Chinese Calendar"),
            ("zodiac", "Western Zodiac"),
            ("angel", "Angel Numbers"),
            ("chaldean", "Chaldean"),
        ]:
            card = OracleCard(parent, title=title)
            card.pack(fill="x", pady=(0, 4))
            self._sign_cards[key] = card

        # Synchronicities
        self._sync_card = OracleCard(parent, title="Synchronicities")
        self._sync_card.pack(fill="x", pady=(0, 4))

        # Interpretation
        self._interp_label = tk.Label(
            parent,
            text="",
            font=FONTS["small"],
            fg=COLORS["text"],
            bg=COLORS["bg"],
            wraplength=500,
            justify="left",
            anchor="nw",
        )
        self._interp_label.pack(fill="x", pady=(0, 4))

    # ─── Name Input ───
    def _build_name_input(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="  Name Cipher  ",
            font=FONTS["body"],
            fg=COLORS["oracle_accent"],
            bg=COLORS["bg_card"],
            bd=1,
            relief="solid",
            padx=12,
            pady=8,
        )
        frame.pack(fill="x", pady=(0, 6))

        row1 = tk.Frame(frame, bg=COLORS["bg_card"])
        row1.pack(fill="x", pady=2)
        tk.Label(
            row1,
            text="Name:",
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
            width=10,
            anchor="e",
        ).pack(side="left")
        self._name_entry = tk.Entry(
            row1,
            font=FONTS["mono"],
            bg=COLORS["bg_input"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            width=24,
        )
        self._name_entry.pack(side="left", padx=(4, 0))

        row2 = tk.Frame(frame, bg=COLORS["bg_card"])
        row2.pack(fill="x", pady=2)
        tk.Label(
            row2,
            text="Birthday:",
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
            width=10,
            anchor="e",
        ).pack(side="left")
        self._bday_entry = tk.Entry(
            row2,
            font=FONTS["mono"],
            bg=COLORS["bg_input"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            width=12,
        )
        self._bday_entry.pack(side="left", padx=(4, 0))

        tk.Label(
            row2,
            text="Mother:",
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
        ).pack(side="left", padx=(8, 0))
        self._mother_entry = tk.Entry(
            row2,
            font=FONTS["mono"],
            bg=COLORS["bg_input"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            width=16,
        )
        self._mother_entry.pack(side="left", padx=(4, 0))

        row3 = tk.Frame(frame, bg=COLORS["bg_card"])
        row3.pack(fill="x", pady=(6, 0))
        StyledButton(
            row3,
            text="Read Name",
            command=self._read_name,
            bg=COLORS["oracle_accent"],
            fg="white",
            font=FONTS["small"],
            padx=12,
            pady=4,
            tooltip="Analyze name using Pythagorean and Chaldean systems",
        ).pack(side="left")

    # ─── Name Display ───
    def _build_name_display(self, parent):
        self._name_card = OracleCard(parent, title="Name Reading")
        self._name_card.pack(fill="x", pady=(0, 4))

    # ─── Daily Insight ───
    def _build_daily_insight(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="  Daily Insight  ",
            font=FONTS["body"],
            fg=COLORS["oracle_accent"],
            bg=COLORS["bg_card"],
            bd=1,
            relief="solid",
            padx=12,
            pady=8,
        )
        frame.pack(fill="x", pady=(0, 4))
        frame.configure(
            highlightbackground=COLORS["oracle_border"],
            highlightthickness=1,
        )

        self._daily_insight_label = tk.Label(
            frame,
            text="Loading...",
            font=FONTS["small"],
            fg=COLORS["text"],
            bg=COLORS["bg_card"],
            wraplength=500,
            justify="left",
            anchor="nw",
        )
        self._daily_insight_label.pack(fill="x")

        self._daily_lucky_label = tk.Label(
            frame,
            text="",
            font=FONTS["mono_sm"],
            fg=COLORS["gold"],
            bg=COLORS["bg_card"],
            anchor="w",
        )
        self._daily_lucky_label.pack(fill="x")

        self._daily_energy_label = tk.Label(
            frame,
            text="",
            font=FONTS["small"],
            fg=COLORS["oracle_accent"],
            bg=COLORS["bg_card"],
            anchor="w",
        )
        self._daily_energy_label.pack(fill="x")

        self._load_daily_insight()

    def _load_daily_insight(self):
        try:
            from engines.oracle import daily_insight

            result = daily_insight()
            self._daily_insight_label.config(text=result.get("insight", ""))
            lucky = result.get("lucky_numbers", [])
            if lucky:
                self._daily_lucky_label.config(
                    text=f"Lucky numbers: {', '.join(str(n) for n in lucky)}"
                )
            energy = result.get("energy", "")
            if energy:
                self._daily_energy_label.config(text=f"Energy: {energy}")
        except Exception:
            self._daily_insight_label.config(text="Daily insight unavailable")

    # ─── AI Panel ───
    def _build_ai_panel(self, parent):
        self._build_daily_insight(parent)
        self.ai_panel = AIInsightPanel(parent, title="AI Interpretation")
        self.ai_panel.pack(fill="x", pady=(0, 4))
        self.ai_panel.set_unavailable()

    # ─── History ───
    def _build_history_panel(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="  Reading History  ",
            font=FONTS["body"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
            bd=1,
            relief="solid",
            padx=8,
            pady=4,
        )
        frame.pack(fill="both", expand=True)

        self._history_listbox = tk.Listbox(
            frame,
            font=FONTS["mono_sm"],
            bg=COLORS["bg_card"],
            fg=COLORS["text"],
            selectbackground=COLORS["bg_hover"],
            height=6,
            bd=0,
        )
        self._history_listbox.pack(fill="both", expand=True)
        self._refresh_history_list()

    # ═══ Actions ═══

    def _read_sign(self):
        """Perform a sign reading (Full or Quick Question mode)."""
        sign = self._sign_entry.get().strip()
        mode = self._reading_mode.get()

        if mode == "question":
            self._read_question_sign(sign)
            return

        date = self._date_entry.get().strip() or None
        time_str = self._time_entry.get().strip() or None

        try:
            from engines.oracle import read_sign

            result = read_sign(sign, date=date, time_str=time_str)
        except Exception as e:
            self._interp_label.config(text=f"Error: {e}", fg=COLORS["error"])
            return

        # Populate system cards
        systems = result.get("systems", {})
        for key, card in self._sign_cards.items():
            card.clear_sections()
            # Map card keys to system dict keys
            sys_key = "numerology" if key == "pythagorean" else key
            data = systems.get(sys_key, {})
            if isinstance(data, dict):
                for k, v in data.items():
                    card.add_section(k, k.replace("_", " ").title(), str(v))
            elif data:
                card.add_section("value", key.title(), str(data))

        # Synchronicities
        self._sync_card.clear_sections()
        syncs = result.get("synchronicities", [])
        for i, s in enumerate(syncs[:5]):
            self._sync_card.add_section(f"sync_{i}", f"#{i+1}", str(s))

        # Interpretation
        interp = result.get("interpretation", "")
        self._interp_label.config(text=interp, fg=COLORS["text"])

        # Save to history
        self._save_reading(
            "sign",
            {
                "sign": sign,
                "date": date,
                "time": time_str,
                "interpretation": interp[:200],
            },
        )

        # AI interpretation
        self._ask_ai_interpretation(f"Sign reading for '{sign}': {interp}")

    def _read_question_sign(self, question):
        """Perform a Quick Question sign reading."""
        if not question:
            self._interp_label.config(
                text="Enter a question or sign text", fg=COLORS["warning"]
            )
            return

        try:
            from engines.oracle import question_sign

            result = question_sign(question)
        except Exception as e:
            self._interp_label.config(text=f"Error: {e}", fg=COLORS["error"])
            return

        # Display reading + advice in interpretation label
        reading = result.get("reading", "")
        advice = result.get("advice", "")
        interp_text = reading
        if advice:
            interp_text += f"\n\nAdvice: {advice}"
        self._interp_label.config(text=interp_text, fg=COLORS["text"])

        # Populate relevant cards from question_sign result
        for key, card in self._sign_cards.items():
            card.clear_sections()

        # Numerology card
        numer = result.get("numerology", {})
        if numer and "pythagorean" in self._sign_cards:
            card = self._sign_cards["pythagorean"]
            numbers = numer.get("numbers", [])
            reduced = numer.get("reduced", [])
            meanings = numer.get("meanings", [])
            for i, n in enumerate(numbers):
                r = reduced[i] if i < len(reduced) else "?"
                m = meanings[i] if i < len(meanings) else ""
                card.add_section(f"n_{i}", f"{n} -> {r}", m)

        # FC60 card
        fc60_data = result.get("fc60", {})
        if fc60_data and "fc60" in self._sign_cards:
            card = self._sign_cards["fc60"]
            code = fc60_data.get("code", "")
            meaning = fc60_data.get("meaning", "")
            if code:
                card.add_section("code", "Code", code)
            if meaning:
                card.add_section("meaning", "Meaning", meaning)

        # Moon card
        moon_data = result.get("moon", {})
        if moon_data and "moon" in self._sign_cards:
            card = self._sign_cards["moon"]
            phase = moon_data.get("phase", "")
            m_meaning = moon_data.get("meaning", "")
            illum = moon_data.get("illumination", 0)
            if phase:
                card.add_section("phase", "Phase", f"{phase} ({illum}%)")
            if m_meaning:
                card.add_section("meaning", "Energy", m_meaning)

        # Clear sync card
        self._sync_card.clear_sections()

        # Save to history
        self._save_reading(
            "question",
            {
                "sign": question,
                "interpretation": reading[:200],
            },
        )

        # AI interpretation
        self._ask_ai_interpretation(
            f"Quick question reading for '{question}': {reading}"
        )

    def _read_name(self):
        """Perform a name reading."""
        name = self._name_entry.get().strip()
        if not name:
            return

        birthday = self._bday_entry.get().strip() or None
        mother = self._mother_entry.get().strip() or None

        try:
            from engines.oracle import read_name

            result = read_name(name, birthday=birthday, mother_name=mother)
        except Exception as e:
            self._name_card.clear_sections()
            self._name_card.add_section("error", "Error", str(e))
            return

        self._name_card.clear_sections()
        for key in ["expression", "soul_urge", "personality", "chaldean", "life_path"]:
            if key in result and result[key] is not None:
                label = key.replace("_", " ").title()
                val = result[key]
                meaning = result.get(f"{key}_meaning", "")
                display = f"{val}" + (f" \u2014 {meaning}" if meaning else "")
                self._name_card.add_section(key, label, display)

        # Mother's influence
        mother_info = result.get("mother_influence")
        if mother_info:
            m_name = mother_info.get("name", "")
            m_expr = mother_info.get("expression", "?")
            m_meaning = mother_info.get("expression_meaning", "")
            display = f"{m_name}: Expression {m_expr}"
            if m_meaning:
                display += f" \u2014 {m_meaning}"
            self._name_card.add_section("mother", "Mother", display)

        # Birthday zodiac
        zodiac = result.get("birthday_zodiac")
        if zodiac:
            z_display = (
                f"{zodiac.get('sign', '')} "
                f"({zodiac.get('element', '')} / {zodiac.get('quality', '')}), "
                f"ruled by {zodiac.get('ruling_planet', '')}"
            )
            self._name_card.add_section("zodiac", "Birthday Zodiac", z_display)

        # Save to history
        self._save_reading(
            "name",
            {
                "name": name,
                "expression": result.get("expression"),
            },
        )

        # AI
        self._ask_ai_interpretation(
            f"Name reading for '{name}': expression={result.get('expression')}, "
            f"soul_urge={result.get('soul_urge')}, personality={result.get('personality')}"
        )

    def _ask_ai_interpretation(self, context):
        """Non-blocking AI interpretation."""
        try:
            from engines.ai_engine import get_ai_insight_async, is_available

            if not is_available():
                return
        except Exception:
            return

        self.ai_panel.set_loading("Generating interpretation...")

        prompt = (
            f"Provide a brief (3-4 sentence) mystical interpretation of this reading:\n"
            f"{context}\n"
            f"Be specific and insightful. Reference the numbers and their meanings."
        )

        def on_result(result):
            self.parent.after(0, self._handle_ai_result, result)

        get_ai_insight_async(prompt, on_result, timeout=15)

    def _handle_ai_result(self, result):
        if result.get("success"):
            self.ai_panel.set_result(
                result["response"],
                result.get("elapsed", 0),
                result.get("cached", False),
            )
        elif result.get("fallback"):
            self.ai_panel.set_result(result.get("response", "\u2014"))
        else:
            self.ai_panel.set_error("AI interpretation unavailable")

    # ═══ History ═══

    def _load_history(self):
        try:
            if self.HISTORY_FILE.exists():
                with open(self.HISTORY_FILE, "r") as f:
                    self._history = json.load(f)
        except Exception:
            self._history = []

    def _save_reading(self, reading_type, data):
        entry = {
            "type": reading_type,
            "timestamp": datetime.now().isoformat(),
            **data,
        }
        self._history.insert(0, entry)
        self._history = self._history[: self.MAX_HISTORY]

        try:
            self.HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.HISTORY_FILE, "w") as f:
                json.dump(self._history, f, indent=2)
        except Exception:
            pass

        self._refresh_history_list()

    def _refresh_history_list(self):
        if not hasattr(self, "_history_listbox"):
            return
        self._history_listbox.delete(0, tk.END)
        for entry in self._history[:20]:
            ts = entry.get("timestamp", "")[:16]
            rtype = entry.get("type", "?")
            if rtype == "sign":
                label = f"{ts}  Sign: {entry.get('sign', '')}"
            else:
                label = f"{ts}  Name: {entry.get('name', '')}"
            self._history_listbox.insert(tk.END, label)
