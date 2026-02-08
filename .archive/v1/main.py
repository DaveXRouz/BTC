"""
BTC Puzzle Hunter + FC60 Translator — Desktop Application
============================================================
Tab 1: BTC Puzzle Hunter — Kangaroo + Smart Brute-Force
Tab 2: FC60 Translator   — FrankenChron-60 Calculation Alphabet

Launch:  python main.py
Requires: Python 3.8+  (no pip installs needed)
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import time
import sys
import os
from datetime import datetime, timezone, timedelta

# Import engines
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import (
    PUZZLES, ECPoint, G, scalar_multiply, decompress_pubkey,
    pubkey_to_address, privkey_to_address, privkey_to_wif,
    KangarooSolver, BruteForceSolver,
    self_test_kangaroo, self_test_bruteforce,
    get_performance_estimate,
)
from fc60_engine import (
    encode_fc60, format_full_output, format_compact_output,
    parse_input, generate_symbolic_reading, generate_personal_reading,
    self_test as fc60_self_test,
    ANIMALS, ANIMAL_NAMES, ELEMENTS, ELEMENT_NAMES,
    WEEKDAYS, WEEKDAY_NAMES, WEEKDAY_PLANETS,
    MOON_PHASES, MOON_PHASE_NAMES,
    token60, digit60, encode_base60, decode_base60,
    life_path, personal_year, name_to_number, name_soul_urge,
    name_personality, LIFE_PATH_MEANINGS, ganzhi_year_name,
)


# ════════════════════════════════════════════════════════════
# Color Theme  (dark, clean, "quiet luxury")
# ════════════════════════════════════════════════════════════

COLORS = {
    'bg':          '#0d1117',
    'bg_card':     '#161b22',
    'bg_input':    '#21262d',
    'bg_button':   '#1f6feb',
    'bg_danger':   '#da3633',
    'bg_success':  '#238636',
    'border':      '#30363d',
    'text':        '#c9d1d9',
    'text_dim':    '#8b949e',
    'text_bright': '#f0f6fc',
    'accent':      '#58a6ff',
    'success':     '#3fb950',
    'warning':     '#d29922',
    'error':       '#f85149',
    'gold':        '#d4a017',
    'purple':      '#a371f7',
}

FONTS = {
    'heading':   ('Segoe UI', 16, 'bold'),
    'subhead':   ('Segoe UI', 12, 'bold'),
    'body':      ('Segoe UI', 10),
    'small':     ('Segoe UI', 9),
    'mono':      ('Consolas', 10),
    'mono_sm':   ('Consolas', 9),
    'mono_lg':   ('Consolas', 11),
    'stat_num':  ('Consolas', 18, 'bold'),
    'tab_title': ('Segoe UI', 11, 'bold'),
}

# Fallback for Linux/Mac
if sys.platform != 'win32':
    for key in FONTS:
        f = list(FONTS[key])
        if f[0] == 'Segoe UI':
            f[0] = 'Helvetica'
        elif f[0] == 'Consolas':
            f[0] = 'Courier'
        FONTS[key] = tuple(f)


# ════════════════════════════════════════════════════════════
# BTC Puzzle Hunter Tab
# ════════════════════════════════════════════════════════════

class PuzzleHunterTab:
    """All BTC Puzzle Hunter logic, rendered inside a tab frame."""

    def __init__(self, parent):
        self.parent = parent
        self.solver = None
        self.worker_thread = None
        self.msg_queue = queue.Queue()
        self.is_running = False
        self.selected_puz = None

        self._build_ui()
        self._poll_queue()
        self._show_welcome()

    def _build_ui(self):
        main = tk.Frame(self.parent, bg=COLORS['bg'], padx=16, pady=12)
        main.pack(fill='both', expand=True)

        # ── Header ──
        header = tk.Frame(main, bg=COLORS['bg'])
        header.pack(fill='x', pady=(0, 12))
        tk.Label(header, text="BTC Puzzle Hunter", font=FONTS['heading'],
                 fg=COLORS['accent'], bg=COLORS['bg']).pack(side='left')
        tk.Label(header, text="Kangaroo + Smart Brute-Force", font=FONTS['small'],
                 fg=COLORS['text_dim'], bg=COLORS['bg']).pack(side='left', padx=(12, 0), pady=(4, 0))

        # ── Top row ──
        top = tk.Frame(main, bg=COLORS['bg'])
        top.pack(fill='x', pady=(0, 8))
        self._build_puzzle_selector(top)
        self._build_controls(top)

        # ── Info Card ──
        self._build_info_card(main)

        # ── Stats ──
        self._build_stats(main)

        # ── Progress ──
        self._build_progress(main)

        # ── Log ──
        self._build_log(main)

    # ── Puzzle Selector ──

    def _build_puzzle_selector(self, parent):
        frame = tk.LabelFrame(parent, text="  Puzzle  ", font=FONTS['body'],
                              fg=COLORS['text_dim'], bg=COLORS['bg_card'],
                              bd=1, relief='solid', padx=12, pady=8)
        frame.pack(side='left', fill='y', padx=(0, 8))

        row1 = tk.Frame(frame, bg=COLORS['bg_card'])
        row1.pack(fill='x')
        tk.Label(row1, text="Select:", font=FONTS['body'],
                 fg=COLORS['text'], bg=COLORS['bg_card']).pack(side='left')

        puzzle_keys = sorted(PUZZLES.keys())
        puzzle_labels = []
        for k in puzzle_keys:
            p = PUZZLES[k]
            status = "✓" if p['solved'] else "○"
            algo = "K" if p['type'] == 'B' else "B"
            puzzle_labels.append(f"#{k}  {status}  [{algo}]  {p['reward_btc']} BTC")

        self.puzzle_var = tk.StringVar()
        self.puzzle_combo = ttk.Combobox(row1, textvariable=self.puzzle_var,
                                         values=puzzle_labels, state='readonly', width=28,
                                         font=FONTS['mono_sm'])
        self.puzzle_combo.pack(side='left', padx=(8, 0))
        self.puzzle_combo.bind('<<ComboboxSelected>>', self._on_puzzle_select)
        if puzzle_labels:
            self.puzzle_combo.current(0)
            self._on_puzzle_select(None)

    # ── Controls ──

    def _build_controls(self, parent):
        frame = tk.LabelFrame(parent, text="  Controls  ", font=FONTS['body'],
                              fg=COLORS['text_dim'], bg=COLORS['bg_card'],
                              bd=1, relief='solid', padx=12, pady=8)
        frame.pack(side='left', fill='both', expand=True)

        btn_row = tk.Frame(frame, bg=COLORS['bg_card'])
        btn_row.pack(fill='x')

        self.btn_start = tk.Button(btn_row, text="▶  Start", font=FONTS['body'],
                                    bg=COLORS['bg_success'], fg='white', activebackground='#2ea043',
                                    bd=0, padx=16, pady=6, cursor='hand2', command=self._start)
        self.btn_start.pack(side='left', padx=(0, 6))

        self.btn_stop = tk.Button(btn_row, text="■  Stop", font=FONTS['body'],
                                   bg=COLORS['bg_danger'], fg='white', activebackground='#b62324',
                                   bd=0, padx=16, pady=6, cursor='hand2', state='disabled', command=self._stop)
        self.btn_stop.pack(side='left', padx=(0, 6))

        self.btn_test = tk.Button(btn_row, text="⚡ Self-Test", font=FONTS['body'],
                                   bg=COLORS['bg_button'], fg='white', activebackground='#1a5cc8',
                                   bd=0, padx=16, pady=6, cursor='hand2', command=self._run_self_test)
        self.btn_test.pack(side='left', padx=(0, 6))

        self.status_label = tk.Label(btn_row, text="⏸ Idle", font=FONTS['small'],
                                      fg=COLORS['text_dim'], bg=COLORS['bg_card'])
        self.status_label.pack(side='right')

    # ── Info Card ──

    def _build_info_card(self, parent):
        self.info_frame = tk.Frame(parent, bg=COLORS['bg_card'], bd=1, relief='solid', padx=12, pady=8)
        self.info_frame.pack(fill='x', pady=(0, 8))

        self.info_labels = {}
        fields = [
            ('puzzle', 'Puzzle:'), ('type', 'Type:'), ('address', 'Address:'),
            ('range', 'Range:'), ('reward', 'Reward:'), ('estimate', 'Estimate:'),
        ]
        for i, (key, label) in enumerate(fields):
            tk.Label(self.info_frame, text=label, font=FONTS['small'],
                     fg=COLORS['text_dim'], bg=COLORS['bg_card']).grid(row=i, column=0, sticky='e', padx=(0, 8))
            lbl = tk.Label(self.info_frame, text="—", font=FONTS['mono_sm'],
                           fg=COLORS['text'], bg=COLORS['bg_card'], anchor='w')
            lbl.grid(row=i, column=1, sticky='w')
            self.info_labels[key] = lbl

        # Public key input
        self.pubkey_frame = tk.Frame(self.info_frame, bg=COLORS['bg_card'])
        self.pubkey_frame.grid(row=len(fields), column=0, columnspan=2, sticky='ew', pady=(4, 0))
        tk.Label(self.pubkey_frame, text="Public Key:", font=FONTS['small'],
                 fg=COLORS['text_dim'], bg=COLORS['bg_card']).pack(side='left')
        self.pubkey_entry = tk.Entry(self.pubkey_frame, font=FONTS['mono_sm'],
                                     bg=COLORS['bg_input'], fg=COLORS['text'],
                                     insertbackground=COLORS['text'], bd=1, relief='solid', width=70)
        self.pubkey_entry.pack(side='left', padx=(8, 0), fill='x', expand=True)
        self.pubkey_frame.grid_remove()

    # ── Stats ──

    def _build_stats(self, parent):
        stats_frame = tk.Frame(parent, bg=COLORS['bg'], pady=4)
        stats_frame.pack(fill='x', pady=(0, 4))

        self.stat_labels = {}
        stat_defs = [
            ('speed', 'Speed', '—'),
            ('operations', 'Operations', '—'),
            ('progress', 'Progress', '—'),
            ('elapsed', 'Elapsed', '—'),
        ]
        for i, (key, title, default) in enumerate(stat_defs):
            card = tk.Frame(stats_frame, bg=COLORS['bg_card'], bd=1, relief='solid', padx=10, pady=4)
            card.pack(side='left', fill='x', expand=True, padx=(0, 6) if i < len(stat_defs) - 1 else 0)
            tk.Label(card, text=title, font=FONTS['small'],
                     fg=COLORS['text_dim'], bg=COLORS['bg_card']).pack()
            lbl = tk.Label(card, text=default, font=FONTS['mono'],
                           fg=COLORS['text_bright'], bg=COLORS['bg_card'])
            lbl.pack()
            self.stat_labels[key] = lbl

    # ── Progress Bar ──

    def _build_progress(self, parent):
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(parent, variable=self.progress_var,
                                             maximum=100, mode='determinate')
        self.progress_bar.pack(fill='x', pady=(0, 8))

    # ── Log ──

    def _build_log(self, parent):
        log_frame = tk.Frame(parent, bg=COLORS['bg'])
        log_frame.pack(fill='both', expand=True)
        self.log_text = scrolledtext.ScrolledText(
            log_frame, bg=COLORS['bg_card'], fg=COLORS['text'], font=FONTS['mono_sm'],
            bd=1, relief='solid', insertbackground=COLORS['text'], wrap='word', height=12)
        self.log_text.pack(fill='both', expand=True)

        for tag, color in [('info', COLORS['text']), ('accent', COLORS['accent']),
                           ('success', COLORS['success']), ('warning', COLORS['warning']),
                           ('error', COLORS['error'])]:
            self.log_text.tag_configure(tag, foreground=color)

    # ── Log helper ──

    def _log(self, text, tag='info'):
        self.log_text.insert('end', text + '\n', tag)
        self.log_text.see('end')

    def _show_welcome(self):
        self._log("Welcome to BTC Puzzle Hunter", 'accent')
        self._log("")
        self._log("Two algorithms available:", 'info')
        self._log("  Kangaroo (K) — O(√n) — for puzzles with known public key", 'info')
        self._log("  Brute-Force (B) — O(n) — for puzzles without public key", 'info')
        self._log("")
        self._log("Quick start:", 'info')
        self._log("  1. Click 'Self-Test' to verify algorithms work", 'info')
        self._log("  2. Select a puzzle from the dropdown", 'info')
        self._log("  3. Click 'Start' to begin scanning", 'info')
        self._log("")
        self._log("Note: Pure Python is great for testing (puzzles ≤40 bits).", 'warning')
        self._log("For real competition, port to C/CUDA for ~10,000x speedup.", 'warning')
        self._log("")

    # ── Puzzle selection ──

    def _on_puzzle_select(self, event):
        sel = self.puzzle_combo.get()
        if not sel:
            return
        num = int(sel.split('#')[1].split()[0])
        self.selected_puz = num
        puz = PUZZLES[num]

        self.info_labels['puzzle'].config(text=f"#{num}")
        self.info_labels['type'].config(
            text=f"Type {'B — Kangaroo eligible ✓' if puz['type'] == 'B' else 'A — Brute-force only'}")
        self.info_labels['address'].config(text=puz['address'])
        self.info_labels['range'].config(text=f"2^{num-1} to 2^{num} ({puz['range_end'] - puz['range_start'] + 1:,} keys)")
        self.info_labels['reward'].config(text=f"{puz['reward_btc']} BTC")

        est = get_performance_estimate(num)
        if est:
            self.info_labels['estimate'].config(text=f"{est['algorithm']}: ~{est['python_human']} (Python)")

        if puz['type'] == 'B':
            self.pubkey_frame.grid()
            if puz.get('public_key'):
                self.pubkey_entry.delete(0, 'end')
                self.pubkey_entry.insert(0, puz['public_key'])
        else:
            self.pubkey_frame.grid_remove()

    # ── State management ──

    def _set_running(self, running):
        self.is_running = running
        if running:
            self.btn_start.config(state='disabled')
            self.btn_stop.config(state='normal')
            self.btn_test.config(state='disabled')
            self.status_label.config(text="⚡ Running", fg=COLORS['success'])
        else:
            self.btn_start.config(state='normal')
            self.btn_stop.config(state='disabled')
            self.btn_test.config(state='normal')
            self.status_label.config(text="⏸ Idle", fg=COLORS['text_dim'])

    # ── Stats update ──

    def _update_stats(self, data):
        speed = data.get('speed', 0)
        if speed > 1000:
            speed_str = f"{speed/1000:.1f}K/s"
        else:
            speed_str = f"{speed:.0f}/s"
        self.stat_labels['speed'].config(text=speed_str)
        self.stat_labels['operations'].config(text=f"{data.get('operations', 0):,}")
        self.stat_labels['progress'].config(text=f"{data.get('progress', 0):.1f}%")

        elapsed = data.get('elapsed', 0)
        if elapsed < 60:
            self.stat_labels['elapsed'].config(text=f"{elapsed:.1f}s")
        elif elapsed < 3600:
            self.stat_labels['elapsed'].config(text=f"{elapsed/60:.1f}m")
        else:
            self.stat_labels['elapsed'].config(text=f"{elapsed/3600:.1f}h")

        self.progress_var.set(data.get('progress', 0))

    # ── Start solving ──

    def _start(self):
        if self.is_running or self.selected_puz is None:
            return

        num = self.selected_puz
        puz = PUZZLES[num]
        self._log("─" * 50, 'info')

        if puz['type'] == 'B':
            pk_hex = self.pubkey_entry.get().strip()
            if not pk_hex:
                self._log("Please paste the public key for this Type B puzzle.", 'error')
                return
            try:
                target_pubkey = decompress_pubkey(pk_hex)
            except Exception as e:
                self._log(f"Invalid public key: {e}", 'error')
                return

            computed_addr = pubkey_to_address(target_pubkey)
            if computed_addr != puz['address']:
                self._log(f"Public key does not match puzzle address!", 'error')
                self._log(f"  Expected: {puz['address']}", 'error')
                self._log(f"  Got:      {computed_addr}", 'error')
                return

            self._log(f"Starting Kangaroo on Puzzle #{num}", 'accent')
            self._log(f"  Range: 2^{num-1} to 2^{num}", 'info')
            self._log(f"  Expected ops: ~{int(2.1 * (2**((num-1)//2))):,}", 'info')
            self._log(f"  Reward: {puz['reward_btc']} BTC", 'warning')

            def progress_cb(data):
                self.msg_queue.put(('stats', data))

            solver = KangarooSolver(target_pubkey, puz['range_start'], puz['range_end'], callback=progress_cb)
        else:
            self._log(f"Starting Brute-Force on Puzzle #{num}", 'accent')
            self._log(f"  Address: {puz['address']}", 'info')
            self._log(f"  Range: 2^{num-1} to 2^{num}", 'info')

            if num > 45:
                self._log(f"  ⚠ Warning: Pure Python brute-force is very slow", 'warning')
                self._log(f"    for puzzles above ~45 bits. Use C/CUDA for real attempts.", 'warning')

            def progress_cb(data):
                self.msg_queue.put(('stats', data))

            solver = BruteForceSolver(puz['address'], puz['range_start'], puz['range_end'], callback=progress_cb)

        self.solver = solver
        self._set_running(True)

        def worker():
            result = solver.solve()
            self.msg_queue.put(('done', result))

        self.worker_thread = threading.Thread(target=worker, daemon=True)
        self.worker_thread.start()

    def _stop(self):
        if self.solver:
            self.solver.stop()
            self._log("Stopping...", 'warning')

    def _on_solved(self, key):
        self._set_running(False)
        if key is None:
            self._log("Stopped without finding solution.", 'info')
            return
        self._log("")
        self._log("═" * 50, 'success')
        self._log("  🎉  PRIVATE KEY FOUND!  🎉", 'success')
        self._log("═" * 50, 'success')
        self._log(f"  Key (hex):  {hex(key)}", 'success')
        self._log(f"  Key (dec):  {key}", 'success')
        self._log(f"  WIF:        {privkey_to_wif(key)}", 'success')
        self._log(f"  Address:    {privkey_to_address(key)}", 'success')
        self._log("═" * 50, 'success')
        self._log("")

        puz = PUZZLES.get(self.selected_puz)
        if puz:
            addr = privkey_to_address(key)
            if addr == puz['address']:
                self._log("✓ Address verified — matches puzzle target!", 'success')
            else:
                self._log("✗ Address mismatch — key may be incorrect", 'error')

    # ── Self-Test ──

    def _run_self_test(self):
        if self.is_running:
            return
        self._set_running(True)
        self._log("")
        self._log("═══ SELF-TEST: Proving algorithms work ═══", 'accent')
        self._log("")

        def progress_cb(data):
            self.msg_queue.put(('stats', data))

        def worker():
            self.msg_queue.put(('log', ('info', "Test 1: Kangaroo algorithm (20-bit range)...")))
            self.msg_queue.put(('log', ('info', "  Generating random key, computing public key...")))
            ok, secret, found, elapsed = self_test_kangaroo(20, callback=progress_cb)
            if ok:
                self.msg_queue.put(('log', ('success', f"  ✓ PASS — Found key {hex(secret)} in {elapsed:.2f}s")))
            else:
                self.msg_queue.put(('log', ('error', f"  ✗ FAIL — Expected {hex(secret)}, got {hex(found) if found else 'None'}")))

            self.msg_queue.put(('log', ('info', "")))
            self.msg_queue.put(('log', ('info', "Test 2: Kangaroo algorithm (24-bit range)...")))
            ok2, secret2, found2, elapsed2 = self_test_kangaroo(24, callback=progress_cb)
            if ok2:
                self.msg_queue.put(('log', ('success', f"  ✓ PASS — Found key {hex(secret2)} in {elapsed2:.2f}s")))
            else:
                self.msg_queue.put(('log', ('error', f"  ✗ FAIL — Expected {hex(secret2)}, got {hex(found2) if found2 else 'None'}")))

            self.msg_queue.put(('log', ('info', "")))
            self.msg_queue.put(('log', ('info', "Test 3: Brute-Force scanner (16-bit range)...")))
            ok3, secret3, found3, elapsed3 = self_test_bruteforce(16, callback=progress_cb)
            if ok3:
                self.msg_queue.put(('log', ('success', f"  ✓ PASS — Found key {hex(secret3)} in {elapsed3:.2f}s")))
            else:
                self.msg_queue.put(('log', ('error', f"  ✗ FAIL — Expected {hex(secret3)}, got {hex(found3) if found3 else 'None'}")))

            all_pass = ok and ok2 and ok3
            self.msg_queue.put(('log', ('info', "")))
            if all_pass:
                self.msg_queue.put(('log', ('success', "═══ ALL TESTS PASSED ✓ ═══")))
                self.msg_queue.put(('log', ('success', "Both algorithms verified working correctly.")))
            else:
                self.msg_queue.put(('log', ('error', "═══ SOME TESTS FAILED ✗ ═══")))
            self.msg_queue.put(('test_done', all_pass))

        self.worker_thread = threading.Thread(target=worker, daemon=True)
        self.worker_thread.start()

    # ── Queue polling ──

    def _poll_queue(self):
        try:
            while True:
                msg_type, data = self.msg_queue.get_nowait()
                if msg_type == 'stats':
                    self._update_stats(data)
                    if data.get('solved') and data.get('solution'):
                        self._on_solved(data['solution'])
                elif msg_type == 'done':
                    if not (self.solver and self.solver.solved):
                        self._on_solved(data)
                    self._set_running(False)
                elif msg_type == 'log':
                    tag, text = data
                    self._log(text, tag)
                elif msg_type == 'test_done':
                    self._set_running(False)
        except queue.Empty:
            pass
        self.parent.after(100, self._poll_queue)


# ════════════════════════════════════════════════════════════
# FC60 Translator Tab
# ════════════════════════════════════════════════════════════

class FC60TranslatorTab:
    """FC60 FrankenChron-60 Translator, rendered inside a tab frame."""

    def __init__(self, parent):
        self.parent = parent
        self._build_ui()

    def _build_ui(self):
        main = tk.Frame(self.parent, bg=COLORS['bg'], padx=16, pady=12)
        main.pack(fill='both', expand=True)

        # ── Header ──
        header = tk.Frame(main, bg=COLORS['bg'])
        header.pack(fill='x', pady=(0, 12))
        tk.Label(header, text="FC60 Translator", font=FONTS['heading'],
                 fg=COLORS['gold'], bg=COLORS['bg']).pack(side='left')
        tk.Label(header, text="FrankenChron-60 • Calculation Alphabet Machine",
                 font=FONTS['small'], fg=COLORS['text_dim'], bg=COLORS['bg']).pack(side='left', padx=(12, 0), pady=(4, 0))

        # ── Top section: Input + Controls ──
        top = tk.Frame(main, bg=COLORS['bg'])
        top.pack(fill='x', pady=(0, 8))

        self._build_translator_input(top)
        self._build_personal_input(top)

        # ── Output ──
        self._build_output(main)

    def _build_translator_input(self, parent):
        frame = tk.LabelFrame(parent, text="  Translate  ", font=FONTS['body'],
                              fg=COLORS['text_dim'], bg=COLORS['bg_card'],
                              bd=1, relief='solid', padx=12, pady=8)
        frame.pack(side='left', fill='both', expand=True, padx=(0, 8))

        # Input row
        row1 = tk.Frame(frame, bg=COLORS['bg_card'])
        row1.pack(fill='x', pady=(0, 6))
        tk.Label(row1, text="Input:", font=FONTS['body'],
                 fg=COLORS['text'], bg=COLORS['bg_card']).pack(side='left')
        self.input_entry = tk.Entry(row1, font=FONTS['mono'], bg=COLORS['bg_input'],
                                     fg=COLORS['text'], insertbackground=COLORS['text'],
                                     bd=1, relief='solid', width=36)
        self.input_entry.pack(side='left', padx=(8, 0), fill='x', expand=True)
        self.input_entry.insert(0, "now")
        self.input_entry.bind('<Return>', lambda e: self._translate())

        # Timezone row
        row2 = tk.Frame(frame, bg=COLORS['bg_card'])
        row2.pack(fill='x', pady=(0, 6))
        tk.Label(row2, text="TZ offset:", font=FONTS['small'],
                 fg=COLORS['text_dim'], bg=COLORS['bg_card']).pack(side='left')
        self.tz_var = tk.StringVar(value="+8")
        tz_entry = tk.Entry(row2, textvariable=self.tz_var, font=FONTS['mono_sm'],
                            bg=COLORS['bg_input'], fg=COLORS['text'],
                            insertbackground=COLORS['text'], bd=1, relief='solid', width=6)
        tz_entry.pack(side='left', padx=(8, 0))
        tk.Label(row2, text="hours  (e.g. +8 = Bali, -5 = NYC, 0 = UTC)",
                 font=FONTS['small'], fg=COLORS['text_dim'], bg=COLORS['bg_card']).pack(side='left', padx=(8, 0))

        # Buttons row
        row3 = tk.Frame(frame, bg=COLORS['bg_card'])
        row3.pack(fill='x')

        tk.Button(row3, text="⚡ Translate", font=FONTS['body'],
                  bg=COLORS['gold'], fg='#0d1117', activebackground='#b8860b',
                  bd=0, padx=16, pady=6, cursor='hand2',
                  command=self._translate).pack(side='left', padx=(0, 6))

        tk.Button(row3, text="🌙 Symbolic", font=FONTS['body'],
                  bg=COLORS['purple'], fg='white', activebackground='#8957e5',
                  bd=0, padx=16, pady=6, cursor='hand2',
                  command=self._symbolic).pack(side='left', padx=(0, 6))

        tk.Button(row3, text="⚡ Self-Test", font=FONTS['body'],
                  bg=COLORS['bg_button'], fg='white', activebackground='#1a5cc8',
                  bd=0, padx=16, pady=6, cursor='hand2',
                  command=self._run_fc60_test).pack(side='left', padx=(0, 6))

        # Input hints
        hints = tk.Frame(frame, bg=COLORS['bg_card'])
        hints.pack(fill='x', pady=(6, 0))
        tk.Label(hints, text="Accepts: now · 2026-02-06 · 2026-02-06T01:15:00+08:00 · 1770394500 · any integer",
                 font=FONTS['small'], fg=COLORS['text_dim'], bg=COLORS['bg_card']).pack(anchor='w')

    def _build_personal_input(self, parent):
        frame = tk.LabelFrame(parent, text="  Personal Reading  ", font=FONTS['body'],
                              fg=COLORS['text_dim'], bg=COLORS['bg_card'],
                              bd=1, relief='solid', padx=12, pady=8)
        frame.pack(side='left', fill='y')

        fields = [
            ("Name:", "name_entry", ""),
            ("DOB:", "dob_entry", "1999-04-22"),
            ("Mother:", "mother_entry", ""),
        ]
        for label_text, attr_name, default in fields:
            row = tk.Frame(frame, bg=COLORS['bg_card'])
            row.pack(fill='x', pady=1)
            tk.Label(row, text=label_text, font=FONTS['small'], fg=COLORS['text_dim'],
                     bg=COLORS['bg_card'], width=7, anchor='e').pack(side='left')
            entry = tk.Entry(row, font=FONTS['mono_sm'], bg=COLORS['bg_input'],
                             fg=COLORS['text'], insertbackground=COLORS['text'],
                             bd=1, relief='solid', width=20)
            entry.pack(side='left', padx=(4, 0))
            if default:
                entry.insert(0, default)
            setattr(self, attr_name, entry)

        tk.Button(frame, text="🔮 Reading", font=FONTS['body'],
                  bg=COLORS['purple'], fg='white', activebackground='#8957e5',
                  bd=0, padx=16, pady=6, cursor='hand2',
                  command=self._personal_reading).pack(fill='x', pady=(6, 0))

    def _build_output(self, parent):
        self.output_text = scrolledtext.ScrolledText(
            parent, bg=COLORS['bg_card'], fg=COLORS['text'], font=FONTS['mono'],
            bd=1, relief='solid', insertbackground=COLORS['text'], wrap='word', height=20)
        self.output_text.pack(fill='both', expand=True)

        for tag, color in [
            ('info', COLORS['text']), ('accent', COLORS['accent']),
            ('success', COLORS['success']), ('warning', COLORS['warning']),
            ('error', COLORS['error']), ('gold', COLORS['gold']),
            ('purple', COLORS['purple']),
        ]:
            self.output_text.tag_configure(tag, foreground=color)

    # ── Helpers ──

    def _out(self, text, tag='info'):
        self.output_text.insert('end', text + '\n', tag)
        self.output_text.see('end')

    def _clear(self):
        self.output_text.delete('1.0', 'end')

    def _get_tz(self):
        try:
            return int(float(self.tz_var.get()))
        except ValueError:
            return 0

    # ── Translate action ──

    def _translate(self):
        self._clear()
        text = self.input_entry.get().strip()
        if not text:
            self._out("Enter a date, time, timestamp, or integer.", 'warning')
            return

        tz_h = self._get_tz()
        self._out(f"Input:  {text}", 'accent')
        self._out(f"TZ:     UTC{'+' if tz_h >= 0 else ''}{tz_h}", 'accent')
        self._out("─" * 55, 'info')

        result = parse_input(text, tz_hours=tz_h)

        if "error" in result:
            self._out(result["error"], 'error')
            return

        if "raw_integer" in result:
            self._out(f"Integer:  {result['raw_integer']}", 'gold')
            self._out(f"Base-60:  {result['base60']}", 'gold')
            if result.get('token60'):
                self._out(f"Mod 60:   {result['token60']}", 'gold')
            return

        if "decoded_integer" in result:
            self._out(f"Decoded:  {result['decoded_integer']}", 'gold')
            return

        # Full FC60 output
        output = format_full_output(result)
        for line in output.split('\n'):
            if line.startswith("FC60:"):
                self._out(line, 'gold')
            elif line.startswith("MOON:"):
                self._out(line, 'purple')
            elif line.startswith("GZ:"):
                self._out(line, 'purple')
            elif line.startswith("CHK:"):
                self._out(line, 'success')
            else:
                self._out(line, 'info')

        # Weekday + planet info
        self._out("")
        self._out(f"  {result['weekday_name']} — {result['weekday_planet']}", 'accent')
        self._out(f"  Domain: {result['weekday_domain']}", 'accent')

    # ── Symbolic reading action ──

    def _symbolic(self):
        self._clear()
        text = self.input_entry.get().strip()
        if not text:
            text = "now"

        tz_h = self._get_tz()
        result = parse_input(text, tz_hours=tz_h)

        if "error" in result or "raw_integer" in result:
            self._out("Symbolic readings require a date/time input.", 'warning')
            return

        # Get the date components from ISO
        iso = result.get('iso', '')
        try:
            parts = iso.split('T')[0].split('-') if 'T' in iso else iso.split('-')
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            if 'T' in iso:
                time_parts = iso.split('T')[1].split('+')[0].split('-')[0].split(':')
                hh = int(time_parts[0])
                mm = int(time_parts[1]) if len(time_parts) > 1 else 0
            else:
                hh, mm = 0, 0
        except (IndexError, ValueError):
            self._out("Could not parse date for symbolic reading.", 'error')
            return

        self._out(f"FC60: {result['stamp']}", 'gold')
        self._out(f"ISO:  {result['iso']}", 'info')
        self._out("")
        self._out("═══ SYMBOLIC READING ═══", 'purple')
        self._out("")

        reading = generate_symbolic_reading(y, m, d, hh, mm)
        for line in reading.split('\n'):
            if line.startswith("⚡") or line.startswith("🔁"):
                self._out(line, 'gold')
            elif line.startswith("Moon:"):
                self._out(line, 'purple')
            elif line.startswith("☀🌙"):
                self._out(line, 'warning')
            else:
                self._out(line, 'info')

    # ── Personal reading action ──

    def _personal_reading(self):
        self._clear()
        name = self.name_entry.get().strip()
        dob = self.dob_entry.get().strip()
        mother = self.mother_entry.get().strip() or None

        if not name:
            self._out("Please enter a name for the personal reading.", 'warning')
            return
        if not dob:
            self._out("Please enter a date of birth (YYYY-MM-DD).", 'warning')
            return

        try:
            parts = dob.split('-')
            by, bm, bd = int(parts[0]), int(parts[1]), int(parts[2])
        except (IndexError, ValueError):
            self._out("Invalid DOB format. Use YYYY-MM-DD.", 'error')
            return

        tz_h = self._get_tz()
        now = datetime.now(timezone(timedelta(hours=tz_h)))

        self._out(f"═══ PERSONAL READING: {name.upper()} ═══", 'gold')
        self._out("")

        reading = generate_personal_reading(
            name, by, bm, bd,
            now.year, now.month, now.day, now.hour, now.minute,
            mother_name=mother,
        )

        for line in reading.split('\n'):
            if line.startswith("═══"):
                self._out(line, 'gold')
            elif any(kw in line for kw in ["Life Path", "Expression", "Soul", "Personality", "Personal Year", "Mother"]):
                self._out(line, 'purple')
            elif line.startswith("⚡") or line.startswith("🔁"):
                self._out(line, 'gold')
            elif line.startswith("Moon:"):
                self._out(line, 'purple')
            elif line.startswith("Birth stamp:") or line.startswith("  Born on"):
                self._out(line, 'accent')
            else:
                self._out(line, 'info')

    # ── FC60 Self-Test ──

    def _run_fc60_test(self):
        self._clear()
        self._out("═══ FC60 ENGINE SELF-TEST ═══", 'accent')
        self._out("")

        results = fc60_self_test()
        passed = 0
        failed = 0

        for test_name, ok, detail in results:
            if ok:
                self._out(f"  ✓ {test_name}", 'success')
                passed += 1
            else:
                self._out(f"  ✗ {test_name}", 'error')
                self._out(f"    {detail}", 'error')
                failed += 1

        self._out("")
        if failed == 0:
            self._out(f"═══ ALL {passed} TESTS PASSED ✓ ═══", 'success')
        else:
            self._out(f"═══ {passed} PASSED, {failed} FAILED ═══", 'error')


# ════════════════════════════════════════════════════════════
# Application (tabbed container)
# ════════════════════════════════════════════════════════════

class Application:

    def __init__(self, root):
        self.root = root
        self.root.title("BTC Puzzle Hunter + FC60 Translator")
        self.root.geometry("1040x780")
        self.root.minsize(900, 650)
        self.root.configure(bg=COLORS['bg'])

        # Style for dark notebook tabs
        style = ttk.Style()
        style.theme_use('default')
        style.configure('Dark.TNotebook', background=COLORS['bg'], borderwidth=0)
        style.configure('Dark.TNotebook.Tab', background=COLORS['bg_card'],
                        foreground=COLORS['text'], padding=[16, 6],
                        font=FONTS['tab_title'])
        style.map('Dark.TNotebook.Tab',
                  background=[('selected', COLORS['bg_input'])],
                  foreground=[('selected', COLORS['text_bright'])])

        # Notebook (tabs)
        self.notebook = ttk.Notebook(root, style='Dark.TNotebook')
        self.notebook.pack(fill='both', expand=True)

        # Tab 1: BTC Puzzle Hunter
        btc_frame = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(btc_frame, text="  ₿  BTC Puzzle Hunter  ")
        self.btc_tab = PuzzleHunterTab(btc_frame)

        # Tab 2: FC60 Translator
        fc60_frame = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(fc60_frame, text="  🔮  FC60 Translator  ")
        self.fc60_tab = FC60TranslatorTab(fc60_frame)


# ════════════════════════════════════════════════════════════
# Entry Point
# ════════════════════════════════════════════════════════════

def main():
    root = tk.Tk()

    # Dark title bar on Windows 10/11
    try:
        import ctypes
        root.update()
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int)
        )
    except Exception:
        pass

    app = Application(root)
    root.mainloop()


if __name__ == '__main__':
    main()
