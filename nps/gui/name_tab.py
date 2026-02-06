"""Name Cipher tab — numerology profile from name + birthday."""

import tkinter as tk
from tkinter import scrolledtext
from gui.theme import COLORS, FONTS
from gui.widgets import StyledButton


class NameTab:
    """Name Cipher — full numerology profile."""

    def __init__(self, parent):
        self.parent = parent
        self._build_ui()

    def _build_ui(self):
        main = tk.Frame(self.parent, bg=COLORS["bg"], padx=16, pady=12)
        main.pack(fill="both", expand=True)

        # Header
        tk.Label(
            main,
            text="Name Cipher",
            font=FONTS["heading"],
            fg=COLORS["accent"],
            bg=COLORS["bg"],
        ).pack(anchor="w", pady=(0, 12))

        # Input panel
        input_frame = tk.LabelFrame(
            main,
            text="  Input  ",
            font=FONTS["body"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
            bd=1,
            relief="solid",
            padx=12,
            pady=8,
        )
        input_frame.pack(fill="x", pady=(0, 12))

        for label_text, attr_name, default, width in [
            ("Full Name:", "name_entry", "", 36),
            ("Birthday (YYYY-MM-DD):", "dob_entry", "1999-04-22", 16),
            ("Mother's Name (optional):", "mother_entry", "", 24),
        ]:
            row = tk.Frame(input_frame, bg=COLORS["bg_card"])
            row.pack(fill="x", pady=2)
            tk.Label(
                row,
                text=label_text,
                font=FONTS["body"],
                fg=COLORS["text"],
                bg=COLORS["bg_card"],
            ).pack(side="left")
            entry = tk.Entry(
                row,
                font=FONTS["mono_sm"],
                bg=COLORS["bg_input"],
                fg=COLORS["text"],
                insertbackground=COLORS["text"],
                bd=1,
                relief="solid",
                width=width,
            )
            entry.pack(side="left", padx=(8, 0))
            if default:
                entry.insert(0, default)
            setattr(self, attr_name, entry)

        StyledButton(
            input_frame,
            text="Generate Reading",
            bg=COLORS["purple"],
            fg="white",
            command=self._generate,
        ).pack(anchor="w", pady=(8, 0))

        # Output
        self.output = scrolledtext.ScrolledText(
            main,
            bg=COLORS["bg_card"],
            fg=COLORS["text"],
            font=FONTS["mono"],
            bd=1,
            relief="solid",
            insertbackground=COLORS["text"],
            wrap="word",
            height=20,
        )
        self.output.pack(fill="both", expand=True)

        for tag, color in [
            ("info", COLORS["text"]),
            ("accent", COLORS["accent"]),
            ("success", COLORS["success"]),
            ("gold", COLORS["gold"]),
            ("purple", COLORS["purple"]),
            ("error", COLORS["error"]),
        ]:
            self.output.tag_configure(tag, foreground=color)

    def _out(self, text, tag="info"):
        self.output.insert("end", text + "\n", tag)
        self.output.see("end")

    def _generate(self):
        self.output.delete("1.0", "end")

        name = self.name_entry.get().strip()
        dob = self.dob_entry.get().strip()
        mother = self.mother_entry.get().strip() or None

        if not name:
            self._out("Please enter a name.", "error")
            return

        birth_year = birth_month = birth_day = None
        if dob:
            try:
                parts = dob.split("-")
                birth_year, birth_month, birth_day = (
                    int(parts[0]),
                    int(parts[1]),
                    int(parts[2]),
                )
            except (IndexError, ValueError):
                self._out("Invalid DOB format. Use YYYY-MM-DD.", "error")
                return

        from solvers.name_solver import NameSolver

        result_data = {}

        def callback(data):
            if data.get("solution"):
                result_data.update(data["solution"])

        solver = NameSolver(
            name,
            birth_year,
            birth_month,
            birth_day,
            mother_name=mother,
            callback=callback,
        )
        solver.running = True
        solver.start_time = __import__("time").time()
        solver.solve()

        if not result_data:
            self._out("Analysis failed.", "error")
            return

        self._out(f"═══ NUMEROLOGY PROFILE: {name.upper()} ═══", "gold")
        self._out("")

        # Core numbers
        for key in ["expression", "soul_urge", "personality"]:
            meaning = result_data.get(f"{key}_meaning", "")
            self._out(f"  {key.replace('_', ' ').title()}: {meaning}", "purple")

        if "life_path_meaning" in result_data:
            self._out(f"  Life Path: {result_data['life_path_meaning']}", "purple")
        if "personal_year_meaning" in result_data:
            self._out(
                f"  Personal Year: {result_data['personal_year_meaning']}", "purple"
            )

        if "mother_meaning" in result_data:
            self._out(
                f"  Mother's Influence: {result_data['mother_meaning']}", "purple"
            )

        self._out("")

        # Letter breakdown
        if "letter_breakdown" in result_data:
            self._out("═══ LETTER BREAKDOWN ═══", "gold")
            self._out(
                f"  {result_data['letter_breakdown']} = {result_data.get('letter_sum', '')}",
                "info",
            )
            self._out(f"  FC60 Token: {result_data.get('fc60_token', '—')}", "accent")
            self._out("")

        # Birth FC60
        if "birth_fc60" in result_data:
            self._out("═══ FC60 BIRTH STAMP ═══", "gold")
            for line in result_data["birth_fc60"].split("\n"):
                self._out(f"  {line}", "info")
            self._out(
                f"  {result_data.get('birth_weekday', '')} — {result_data.get('birth_planet', '')}",
                "accent",
            )
            self._out(f"  Domain: {result_data.get('birth_domain', '')}", "accent")
            self._out(f"  Birth Year: {result_data.get('birth_gz', '')}", "purple")
            self._out("")

        # Full reading
        if "full_reading" in result_data:
            self._out("═══ CURRENT MOMENT READING ═══", "gold")
            for line in result_data["full_reading"].split("\n"):
                if line.startswith("═══"):
                    self._out(line, "gold")
                elif "⚡" in line or "🔁" in line:
                    self._out(line, "gold")
                elif "Moon:" in line:
                    self._out(line, "purple")
                else:
                    self._out(line, "info")

        # AI personalized reading
        if result_data.get("ai_reading"):
            self._out("")
            self._out("═══ AI PERSONALIZED READING ═══", "purple")
            for line in result_data["ai_reading"].split("\n"):
                if line.strip():
                    self._out(f"  {line}", "purple")
            meta = ""
            if result_data.get("ai_cached"):
                meta = "(cached)"
            elif result_data.get("ai_elapsed", 0) > 0:
                meta = f"({result_data['ai_elapsed']:.1f}s)"
            if meta:
                self._out(f"  {meta}", "info")
