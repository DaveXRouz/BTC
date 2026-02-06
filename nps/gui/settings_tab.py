"""
Settings & Connections Tab for NPS V3.

Covers: Telegram config, security management, deployment,
scanner defaults, notification toggles, and about info.
"""

import tkinter as tk
import logging

logger = logging.getLogger(__name__)


class SettingsTab:
    """Fifth tab: Settings & Connections."""

    def __init__(self, parent, app=None):
        self.parent = parent
        self.app = app

        from gui.theme import COLORS, FONTS

        self.COLORS = COLORS
        self.FONTS = FONTS

        self._build_ui()

    def _build_ui(self):
        C = self.COLORS
        F = self.FONTS

        # Scrollable canvas
        canvas = tk.Canvas(self.parent, bg=C["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.parent, orient="vertical", command=canvas.yview)
        self.content = tk.Frame(canvas, bg=C["bg"])

        self.content.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        pad = {"padx": 16, "pady": 8}

        # ── Telegram Section ──
        self._section_label("Telegram Notifications")

        tg_frame = tk.Frame(self.content, bg=C["bg_card"], bd=1, relief="solid")
        tg_frame.pack(fill="x", **pad)

        # Bot Token (masked)
        tk.Label(
            tg_frame, text="Bot Token:", font=F["small"], fg=C["text"], bg=C["bg_card"]
        ).grid(row=0, column=0, sticky="w", padx=8, pady=4)

        self.token_var = tk.StringVar()
        self.token_entry = tk.Entry(
            tg_frame,
            textvariable=self.token_var,
            show="*",
            font=F["small"],
            bg=C["bg_input"],
            fg=C["text"],
            insertbackground=C["text"],
            width=40,
        )
        self.token_entry.grid(row=0, column=1, padx=8, pady=4)

        # Chat ID
        tk.Label(
            tg_frame, text="Chat ID:", font=F["small"], fg=C["text"], bg=C["bg_card"]
        ).grid(row=1, column=0, sticky="w", padx=8, pady=4)

        self.chat_var = tk.StringVar()
        tk.Entry(
            tg_frame,
            textvariable=self.chat_var,
            font=F["small"],
            bg=C["bg_input"],
            fg=C["text"],
            insertbackground=C["text"],
            width=40,
        ).grid(row=1, column=1, padx=8, pady=4)

        # Test + Save buttons
        btn_frame = tk.Frame(tg_frame, bg=C["bg_card"])
        btn_frame.grid(row=2, column=0, columnspan=2, pady=8)

        tk.Button(
            btn_frame,
            text="Test Connection",
            command=self._test_telegram,
            bg=C["bg_input"],
            fg=C["text"],
            font=F["small"],
        ).pack(side="left", padx=4)

        tk.Button(
            btn_frame,
            text="Save",
            command=self._save_telegram,
            bg=C["bg_success"],
            fg="white",
            font=F["small"],
        ).pack(side="left", padx=4)

        self.tg_status = tk.Label(
            tg_frame, text="", font=F["small"], fg=C["text_dim"], bg=C["bg_card"]
        )
        self.tg_status.grid(row=3, column=0, columnspan=2, pady=4)

        # ── Security Section ──
        self._section_label("Security")

        sec_frame = tk.Frame(self.content, bg=C["bg_card"], bd=1, relief="solid")
        sec_frame.pack(fill="x", **pad)

        try:
            from engines.security import is_encrypted_mode

            enc_status = "Encrypted" if is_encrypted_mode() else "Not Encrypted"
        except Exception:
            enc_status = "Not Available"

        tk.Label(
            sec_frame,
            text=f"Status: {enc_status}",
            font=F["small"],
            fg=C["text"],
            bg=C["bg_card"],
        ).pack(anchor="w", padx=8, pady=4)

        # ── Scanner Settings ──
        self._section_label("Scanner Defaults")

        scan_frame = tk.Frame(self.content, bg=C["bg_card"], bd=1, relief="solid")
        scan_frame.pack(fill="x", **pad)

        settings = [
            ("Batch Size:", "scanner.batch_size", "1000"),
            ("Check Every N:", "scanner.check_every_n", "5000"),
            ("Threads:", "scanner.threads", "1"),
        ]

        self.scan_vars = {}
        for i, (label, key, default) in enumerate(settings):
            tk.Label(
                scan_frame,
                text=label,
                font=F["small"],
                fg=C["text"],
                bg=C["bg_card"],
            ).grid(row=i, column=0, sticky="w", padx=8, pady=2)

            var = tk.StringVar(value=self._get_config(key, default))
            self.scan_vars[key] = var
            tk.Entry(
                scan_frame,
                textvariable=var,
                font=F["small"],
                bg=C["bg_input"],
                fg=C["text"],
                insertbackground=C["text"],
                width=10,
            ).grid(row=i, column=1, padx=8, pady=2)

        tk.Button(
            scan_frame,
            text="Save Scanner Settings",
            command=self._save_scanner_settings,
            bg=C["bg_success"],
            fg="white",
            font=F["small"],
        ).grid(row=len(settings), column=0, columnspan=2, pady=8)

        # ── Reset ──
        self._section_label("Danger Zone")

        reset_frame = tk.Frame(self.content, bg=C["bg_card"], bd=1, relief="solid")
        reset_frame.pack(fill="x", **pad)

        tk.Button(
            reset_frame,
            text="Reset to Defaults",
            command=self._reset_defaults,
            bg=C["bg_danger"],
            fg="white",
            font=F["small"],
        ).pack(padx=8, pady=8)

        # ── About ──
        self._section_label("About")

        about_frame = tk.Frame(self.content, bg=C["bg_card"], bd=1, relief="solid")
        about_frame.pack(fill="x", **pad)

        try:
            from engines.config import get_config_path

            config_path = get_config_path()
        except Exception:
            config_path = "unknown"

        tk.Label(
            about_frame,
            text="NPS — Numerology Puzzle Solver V3",
            font=F["small"],
            fg=C["text"],
            bg=C["bg_card"],
        ).pack(anchor="w", padx=8, pady=2)
        tk.Label(
            about_frame,
            text=f"Config: {config_path}",
            font=F["small"],
            fg=C["text_dim"],
            bg=C["bg_card"],
        ).pack(anchor="w", padx=8, pady=2)

        # Load current values
        self._load_current_values()

    def _section_label(self, text):
        C = self.COLORS
        F = self.FONTS
        tk.Label(
            self.content,
            text=text,
            font=F.get("card_title", F["small"]),
            fg=C["text_bright"],
            bg=C["bg"],
        ).pack(anchor="w", padx=16, pady=(12, 2))

    def _get_config(self, key, default=""):
        try:
            from engines.config import get

            val = get(key, default)
            return str(val)
        except Exception:
            return default

    def _load_current_values(self):
        """Load current config values into UI fields."""
        try:
            from engines.config import get_bot_token, get_chat_id

            self.token_var.set(get_bot_token() or "")
            self.chat_var.set(get_chat_id() or "")
        except Exception:
            pass

    def _test_telegram(self):
        """Test Telegram connection."""
        C = self.COLORS
        try:
            from engines.notifier import send_message, is_configured

            if is_configured():
                result = send_message("NPS Settings Test — Connection OK")
                if result:
                    self.tg_status.config(
                        text="Connection successful!", fg=C["success"]
                    )
                else:
                    self.tg_status.config(text="Send failed", fg=C["error"])
            else:
                self.tg_status.config(
                    text="Not configured (set chat_id)", fg=C["warning"]
                )
        except Exception as e:
            self.tg_status.config(text=f"Error: {e}", fg=C["error"])

    def _save_telegram(self):
        """Save Telegram settings."""
        try:
            from engines.config import save_config_updates

            updates = {
                "telegram": {
                    "bot_token": self.token_var.get(),
                    "chat_id": self.chat_var.get(),
                }
            }
            save_config_updates(updates)
            self.tg_status.config(text="Saved!", fg=self.COLORS["success"])
        except Exception as e:
            self.tg_status.config(text=f"Save failed: {e}", fg=self.COLORS["error"])

    def _save_scanner_settings(self):
        """Save scanner settings to config."""
        try:
            from engines.config import save_config_updates

            updates = {"scanner": {}}
            for key, var in self.scan_vars.items():
                _, field = key.split(".", 1)
                try:
                    updates["scanner"][field] = int(var.get())
                except ValueError:
                    updates["scanner"][field] = var.get()
            save_config_updates(updates)
        except Exception as e:
            logger.error(f"Save scanner settings failed: {e}")

    def _reset_defaults(self):
        """Reset config to defaults."""
        try:
            from engines.config import reset_defaults

            reset_defaults()
            self._load_current_values()
        except Exception as e:
            logger.error(f"Reset defaults failed: {e}")
