"""
Settings & Connections Tab for NPS V3.

Covers: Telegram config, security management, deployment,
scanner defaults, notification toggles, and about info.
"""

import threading
import tkinter as tk
from tkinter import ttk, filedialog
import logging
from gui.widgets import StyledButton

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

        # Enabled toggle
        self._tg_enabled_var = tk.BooleanVar(
            value=self._get_config_bool("telegram.enabled", True)
        )
        tk.Checkbutton(
            tg_frame,
            text="Enable Notifications",
            variable=self._tg_enabled_var,
            font=F["small"],
            fg=C["text"],
            bg=C["bg_card"],
            selectcolor=C["bg_input"],
            activebackground=C["bg_card"],
            activeforeground=C["text"],
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=4)

        # Bot Token (masked)
        tk.Label(
            tg_frame, text="Bot Token:", font=F["small"], fg=C["text"], bg=C["bg_card"]
        ).grid(row=1, column=0, sticky="w", padx=8, pady=4)

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
        self.token_entry.grid(row=1, column=1, padx=8, pady=4)

        # Chat ID
        tk.Label(
            tg_frame, text="Chat ID:", font=F["small"], fg=C["text"], bg=C["bg_card"]
        ).grid(row=2, column=0, sticky="w", padx=8, pady=4)

        self.chat_var = tk.StringVar()
        tk.Entry(
            tg_frame,
            textvariable=self.chat_var,
            font=F["small"],
            bg=C["bg_input"],
            fg=C["text"],
            insertbackground=C["text"],
            width=40,
        ).grid(row=2, column=1, padx=8, pady=4)

        # Per-type notification toggles
        self._notify_balance_var = tk.BooleanVar(
            value=self._get_config_bool("telegram.notify_balance", True)
        )
        self._notify_error_var = tk.BooleanVar(
            value=self._get_config_bool("telegram.notify_error", True)
        )
        self._notify_daily_var = tk.BooleanVar(
            value=self._get_config_bool("telegram.notify_daily", True)
        )

        toggle_frame = tk.Frame(tg_frame, bg=C["bg_card"])
        toggle_frame.grid(row=3, column=0, columnspan=2, sticky="w", padx=8, pady=2)
        for var, label in [
            (self._notify_balance_var, "Balance found"),
            (self._notify_error_var, "Errors"),
            (self._notify_daily_var, "Daily status"),
        ]:
            tk.Checkbutton(
                toggle_frame,
                text=label,
                variable=var,
                font=F["small"],
                fg=C["text"],
                bg=C["bg_card"],
                selectcolor=C["bg_input"],
                activebackground=C["bg_card"],
                activeforeground=C["text"],
            ).pack(side="left", padx=(0, 12))

        # Test + Save buttons
        btn_frame = tk.Frame(tg_frame, bg=C["bg_card"])
        btn_frame.grid(row=4, column=0, columnspan=2, pady=8)

        StyledButton(
            btn_frame,
            text="Test Connection",
            command=self._test_telegram,
            bg=C["accent"],
            fg=C["text_bright"],
            font=F["small"],
            padx=8,
            pady=3,
            tooltip="Send a test message to verify Telegram setup",
        ).pack(side="left", padx=4)

        StyledButton(
            btn_frame,
            text="Save",
            command=self._save_telegram,
            bg=C["bg_success"],
            fg=C["text_bright"],
            font=F["small"],
            padx=8,
            pady=3,
            tooltip="Save Telegram bot token, chat ID, and notification settings",
        ).pack(side="left", padx=4)

        self.tg_status = tk.Label(
            tg_frame, text="", font=F["small"], fg=C["text_dim"], bg=C["bg_card"]
        )
        self.tg_status.grid(row=5, column=0, columnspan=2, pady=4)

        # ── Security Section ──
        self._section_label("Security")

        sec_frame = tk.Frame(self.content, bg=C["bg_card"], bd=1, relief="solid")
        sec_frame.pack(fill="x", **pad)

        try:
            from engines.security import is_encrypted_mode

            enc_status = "Encrypted" if is_encrypted_mode() else "Not Encrypted"
        except Exception:
            enc_status = "Not Available"

        self._sec_status_label = tk.Label(
            sec_frame,
            text=f"Status: {enc_status}",
            font=F["body"],
            fg=C["text_bright"],
            bg=C["bg_card"],
        )
        self._sec_status_label.pack(anchor="w", padx=8, pady=4)

        StyledButton(
            sec_frame,
            text="Change Master Key",
            command=self._change_master_key,
            bg=C["bg_button"],
            fg=C["text_bright"],
            tooltip="Change the encryption master key for vault data",
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

        StyledButton(
            scan_frame,
            text="Save Scanner Settings",
            command=self._save_scanner_settings,
            bg=C["bg_success"],
            fg=C["text_bright"],
            font=F["small"],
            padx=8,
            pady=3,
        ).grid(row=len(settings), column=0, columnspan=2, pady=8)

        # ── Deployment (Headless) ──
        self._section_label("Deployment (Headless)")

        deploy_frame = tk.Frame(self.content, bg=C["bg_card"], bd=1, relief="solid")
        deploy_frame.pack(fill="x", **pad)

        self._deploy_auto_start = tk.BooleanVar(
            value=self._get_config_bool("headless.auto_start_scanner", True)
        )
        tk.Checkbutton(
            deploy_frame,
            text="Auto-start scanner",
            variable=self._deploy_auto_start,
            font=F["small"],
            fg=C["text"],
            bg=C["bg_card"],
            selectcolor=C["bg_input"],
            activebackground=C["bg_card"],
            activeforeground=C["text"],
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=2)

        tk.Label(
            deploy_frame,
            text="Scanner Mode:",
            font=F["small"],
            fg=C["text"],
            bg=C["bg_card"],
        ).grid(row=1, column=0, sticky="w", padx=8, pady=2)
        self._deploy_mode_var = tk.StringVar(
            value=self._get_config("headless.scanner_mode", "both")
        )
        ttk.Combobox(
            deploy_frame,
            textvariable=self._deploy_mode_var,
            values=["random_key", "seed_phrase", "both"],
            state="readonly",
            width=14,
            font=F["small"],
        ).grid(row=1, column=1, padx=8, pady=2)

        tk.Label(
            deploy_frame,
            text="Status Interval (hrs):",
            font=F["small"],
            fg=C["text"],
            bg=C["bg_card"],
        ).grid(row=2, column=0, sticky="w", padx=8, pady=2)
        self._deploy_interval_var = tk.StringVar(
            value=self._get_config("headless.status_interval_hours", "24")
        )
        tk.Entry(
            deploy_frame,
            textvariable=self._deploy_interval_var,
            font=F["small"],
            bg=C["bg_input"],
            fg=C["text"],
            insertbackground=C["text"],
            width=10,
        ).grid(row=2, column=1, padx=8, pady=2)

        self._deploy_daily_var = tk.BooleanVar(
            value=self._get_config_bool("headless.daily_status", True)
        )
        tk.Checkbutton(
            deploy_frame,
            text="Daily status report",
            variable=self._deploy_daily_var,
            font=F["small"],
            fg=C["text"],
            bg=C["bg_card"],
            selectcolor=C["bg_input"],
            activebackground=C["bg_card"],
            activeforeground=C["text"],
        ).grid(row=3, column=0, columnspan=2, sticky="w", padx=8, pady=2)

        StyledButton(
            deploy_frame,
            text="Save Deployment Settings",
            command=self._save_deployment_settings,
            bg=C["bg_success"],
            fg=C["text_bright"],
            font=F["small"],
            padx=8,
            pady=3,
        ).grid(row=4, column=0, columnspan=2, pady=8)

        # ── Reset ──
        self._section_label("Danger Zone")

        reset_frame = tk.Frame(self.content, bg=C["bg_card"], bd=1, relief="solid")
        reset_frame.pack(fill="x", **pad)

        StyledButton(
            reset_frame,
            text="Reset to Defaults",
            command=self._reset_defaults,
            bg=C["bg_danger"],
            fg=C["text_bright"],
            font=F["small"],
            padx=8,
            pady=3,
            tooltip="Reset all settings to factory defaults",
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

        # Export / Import buttons
        cfg_btn_frame = tk.Frame(about_frame, bg=C["bg_card"])
        cfg_btn_frame.pack(fill="x", padx=8, pady=4)

        StyledButton(
            cfg_btn_frame,
            text="Export Config",
            command=self._export_config,
            bg=C["bg_button"],
            fg=C["text_bright"],
            font=F["small"],
            padx=8,
            pady=3,
            tooltip="Export configuration to a JSON file",
        ).pack(side="left", padx=4)

        StyledButton(
            cfg_btn_frame,
            text="Import Config",
            command=self._import_config,
            bg=C["bg_button"],
            fg=C["text_bright"],
            font=F["small"],
            padx=8,
            pady=3,
            tooltip="Import configuration from a JSON file",
        ).pack(side="left", padx=4)

        # Load current values
        self._load_current_values()

    def _section_label(self, text):
        C = self.COLORS
        F = self.FONTS
        tk.Label(
            self.content,
            text=text,
            font=F["subhead"],
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

    def _get_config_bool(self, key, default=True):
        try:
            from engines.config import get

            return bool(get(key, default))
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
        """Test Telegram connection in a background thread."""
        C = self.COLORS
        self.tg_status.config(text="Testing...", fg=C["text_dim"])

        def _do_test():
            try:
                from engines.notifier import send_message, is_configured

                if is_configured():
                    result = send_message("NPS Settings Test — Connection OK")
                    if result:
                        self.parent.after(
                            0,
                            lambda: self.tg_status.config(
                                text="Connection successful!", fg=C["success"]
                            ),
                        )
                    else:
                        self.parent.after(
                            0,
                            lambda: self.tg_status.config(
                                text="Send failed", fg=C["error"]
                            ),
                        )
                else:
                    self.parent.after(
                        0,
                        lambda: self.tg_status.config(
                            text="Not configured (set chat_id)", fg=C["warning"]
                        ),
                    )
            except Exception as e:
                self.parent.after(
                    0,
                    lambda: self.tg_status.config(text=f"Error: {e}", fg=C["error"]),
                )

        threading.Thread(target=_do_test, daemon=True).start()

    def _save_telegram(self):
        """Save Telegram settings including notification toggles."""
        try:
            from engines.config import save_config_updates

            updates = {
                "telegram": {
                    "bot_token": self.token_var.get(),
                    "chat_id": self.chat_var.get(),
                    "enabled": self._tg_enabled_var.get(),
                    "notify_balance": self._notify_balance_var.get(),
                    "notify_error": self._notify_error_var.get(),
                    "notify_daily": self._notify_daily_var.get(),
                }
            }
            save_config_updates(updates)
            self.tg_status.config(text="Saved!", fg=self.COLORS["success"])
            try:
                from engines.events import emit, CONFIG_CHANGED

                emit(CONFIG_CHANGED, {"section": "telegram"})
            except Exception:
                pass
        except Exception as e:
            self.tg_status.config(text=f"Save failed: {e}", fg=self.COLORS["error"])

    def _change_master_key(self):
        """Show change master key dialog."""
        try:
            from gui.widgets import ask_change_password
            from engines.security import change_master_password

            result = ask_change_password(self.parent)
            if result is None:
                return

            old_key, new_key = result
            try:
                change_master_password(old_key, new_key)
                self._sec_status_label.config(
                    text="Status: Encrypted (key changed)",
                    fg=self.COLORS["success"],
                )
            except ValueError as e:
                self._sec_status_label.config(
                    text=f"Error: {e}",
                    fg=self.COLORS["error"],
                )
        except Exception as e:
            self._sec_status_label.config(
                text=f"Error: {e}",
                fg=self.COLORS["error"],
            )

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
            try:
                from engines.events import emit, CONFIG_CHANGED

                emit(CONFIG_CHANGED, {"section": "scanner"})
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Save scanner settings failed: {e}")

    def _save_deployment_settings(self):
        """Save deployment/headless settings to config."""
        try:
            from engines.config import save_config_updates

            interval = self._deploy_interval_var.get()
            try:
                interval = int(interval)
            except ValueError:
                interval = 24

            updates = {
                "headless": {
                    "auto_start_scanner": self._deploy_auto_start.get(),
                    "scanner_mode": self._deploy_mode_var.get(),
                    "status_interval_hours": interval,
                    "daily_status": self._deploy_daily_var.get(),
                }
            }
            save_config_updates(updates)
        except Exception as e:
            logger.error(f"Save deployment settings failed: {e}")

    def _export_config(self):
        """Export config to a user-selected file."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile="nps_config_export.json",
        )
        if not filepath:
            return

        try:
            from engines.config import save_config

            save_config(path=filepath)
        except Exception as e:
            logger.error(f"Export config failed: {e}")

    def _import_config(self):
        """Import config from a user-selected file."""
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")],
        )
        if not filepath:
            return

        try:
            from engines.config import load_config

            load_config(path=filepath)
            self._load_current_values()
        except Exception as e:
            logger.error(f"Import config failed: {e}")

    def _reset_defaults(self):
        """Reset config to defaults."""
        try:
            from engines.config import reset_defaults

            reset_defaults()
            self._load_current_values()
        except Exception as e:
            logger.error(f"Reset defaults failed: {e}")
