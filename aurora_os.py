"""
AuroraOS MVP - A minimal Windows-12-inspired desktop in Python/Tkinter.
Run: python aurora_os.py
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import datetime
import math
import random
import time
import threading


# ── Palette ──────────────────────────────────────────────────────────────────
BG          = "#0b0f1e"
PANEL       = "#111827"
PANEL2      = "#1a2236"
BORDER      = "#1e2d45"
ACCENT      = "#4facfe"
ACCENT2     = "#a78bfa"
TEXT        = "#e2e8f0"
TEXT_DIM    = "#64748b"
TEXT_BRIGHT = "#f8fafc"
TITLEBAR    = "#0d1629"
WIN_BG      = "#0f172a"
BTN_CLOSE   = "#ef4444"
BTN_MIN     = "#f59e0b"
BTN_MAX     = "#22c55e"
FONT        = ("Segoe UI", 10)
FONT_SM     = ("Segoe UI", 9)
FONT_LG     = ("Segoe UI", 13, "bold")
FONT_MONO   = ("Consolas", 10)


# ── Desktop Shell ─────────────────────────────────────────────────────────────
class AuroraOS:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AuroraOS")
        self.root.configure(bg=BG)
        self.root.geometry("1280x800")
        self.root.minsize(900, 600)

        self.windows = []       # open app windows
        self.taskbar_btns = {}  # appid -> button

        self._build_desktop()
        self._build_taskbar()
        self._start_clock()

    # ── Desktop canvas (wallpaper + icons) ───────────────────────────────────
    def _build_desktop(self):
        self.desktop = tk.Canvas(self.root, bg=BG, highlightthickness=0)
        self.desktop.pack(fill=tk.BOTH, expand=True)
        self.desktop.bind("<Configure>", self._draw_wallpaper)

        # Desktop app icons
        icons = [
            ("📁", "Files",       self.open_files),
            ("📝", "Notes",       self.open_notes),
            ("⚡", "Terminal",    self.open_terminal),
            ("🔢", "Calculator",  self.open_calculator),
            ("⚙️", "Settings",    self.open_settings),
            ("📊", "Monitor",     self.open_monitor),
        ]
        for i, (ico, label, cmd) in enumerate(icons):
            row, col = divmod(i, 1)
            x, y = 30, 30 + i * 90
            self._desktop_icon(x, y, ico, label, cmd)

    def _draw_wallpaper(self, event=None):
        w = self.desktop.winfo_width()
        h = self.desktop.winfo_height()
        self.desktop.delete("wallpaper")
        # Simple gradient simulation with rectangles
        steps = 32
        for i in range(steps):
            t = i / steps
            r = int(11  + t * 5)
            g = int(15  + t * 20)
            b = int(30  + t * 60)
            color = f"#{r:02x}{g:02x}{b:02x}"
            self.desktop.create_rectangle(
                0, int(h * i / steps), w, int(h * (i + 1) / steps),
                fill=color, outline="", tags="wallpaper"
            )
        # Subtle glow orb top-right
        self.desktop.create_oval(w - 300, -100, w + 100, 300,
            fill="#0d2550", outline="", tags="wallpaper")
        self.desktop.tag_lower("wallpaper")

    def _desktop_icon(self, x, y, emoji, label, command):
        frame = tk.Frame(self.desktop, bg=BG, cursor="hand2")
        lbl_ico = tk.Label(frame, text=emoji, font=("Segoe UI Emoji", 24),
                           bg=BG, fg=TEXT)
        lbl_ico.pack()
        lbl_txt = tk.Label(frame, text=label, font=FONT_SM, bg=BG, fg=TEXT,
                           width=8)
        lbl_txt.pack()
        frame.bind("<Button-1>", lambda e: command())
        lbl_ico.bind("<Button-1>", lambda e: command())
        lbl_txt.bind("<Button-1>", lambda e: command())

        # Hover highlight
        def on_enter(e):
            for w in [frame, lbl_ico, lbl_txt]:
                w.configure(bg="#1e2d45")
        def on_leave(e):
            for w in [frame, lbl_ico, lbl_txt]:
                w.configure(bg=BG)
        for w in [frame, lbl_ico, lbl_txt]:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)

        self.desktop.create_window(x, y, anchor="nw", window=frame)

    # ── Taskbar ───────────────────────────────────────────────────────────────
    def _build_taskbar(self):
        self.taskbar = tk.Frame(self.root, bg=PANEL, height=56,
                                relief="flat")
        self.taskbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.taskbar.pack_propagate(False)

        # Left: Start button
        self.start_btn = tk.Button(
            self.taskbar, text="⊞  Aurora", font=("Segoe UI", 10, "bold"),
            bg=PANEL, fg=ACCENT, activebackground=PANEL2,
            activeforeground=ACCENT, bd=0, padx=16, pady=8, cursor="hand2",
            command=self._toggle_start_menu
        )
        self.start_btn.pack(side=tk.LEFT, padx=(8, 4), pady=8)

        # Separator
        tk.Frame(self.taskbar, bg=BORDER, width=1).pack(
            side=tk.LEFT, fill=tk.Y, pady=10)

        # Center: quick-launch dock
        dock_apps = [
            ("📁", "Files",      self.open_files),
            ("📝", "Notes",      self.open_notes),
            ("⚡", "Terminal",   self.open_terminal),
            ("🔢", "Calc",       self.open_calculator),
            ("⚙️", "Settings",   self.open_settings),
        ]
        self.dock_frame = tk.Frame(self.taskbar, bg=PANEL)
        self.dock_frame.pack(side=tk.LEFT, padx=8)
        for ico, tip, cmd in dock_apps:
            b = tk.Button(self.dock_frame, text=ico,
                          font=("Segoe UI Emoji", 16),
                          bg=PANEL, fg=TEXT, activebackground=PANEL2,
                          bd=0, padx=8, pady=6, cursor="hand2",
                          command=cmd)
            b.pack(side=tk.LEFT)
            self._add_tooltip(b, tip)

        # Right: clock + date
        self.clock_var = tk.StringVar()
        self.date_var  = tk.StringVar()
        right = tk.Frame(self.taskbar, bg=PANEL)
        right.pack(side=tk.RIGHT, padx=16)
        tk.Label(right, textvariable=self.clock_var, font=("Segoe UI", 11, "bold"),
                 bg=PANEL, fg=TEXT_BRIGHT).pack(anchor="e")
        tk.Label(right, textvariable=self.date_var, font=FONT_SM,
                 bg=PANEL, fg=TEXT_DIM).pack(anchor="e")

        # Notification dot
        self.notif_btn = tk.Button(
            self.taskbar, text="🔔", font=("Segoe UI Emoji", 14),
            bg=PANEL, fg=TEXT_DIM, activebackground=PANEL2,
            bd=0, padx=8, pady=8, cursor="hand2",
            command=self._show_notification
        )
        self.notif_btn.pack(side=tk.RIGHT, pady=8)

    def _start_clock(self):
        def tick():
            now = datetime.datetime.now()
            self.clock_var.set(now.strftime("%H:%M"))
            self.date_var.set(now.strftime("%a, %b %d"))
            self.root.after(10000, tick)
        tick()

    def _add_tooltip(self, widget, text):
        def show(e):
            tip = tk.Toplevel(self.root)
            tip.wm_overrideredirect(True)
            tip.configure(bg=PANEL2)
            tk.Label(tip, text=text, font=FONT_SM, bg=PANEL2, fg=TEXT,
                     padx=8, pady=4).pack()
            x = widget.winfo_rootx() + 20
            y = widget.winfo_rooty() - 36
            tip.geometry(f"+{x}+{y}")
            widget._tip = tip
        def hide(e):
            if hasattr(widget, "_tip"):
                widget._tip.destroy()
        widget.bind("<Enter>", show)
        widget.bind("<Leave>", hide)

    def _show_notification(self):
        msgs = [
            "⚡  AuroraOS is up to date.",
            "📦  No pending updates.",
            "🔋  Battery: 87% — plugged in.",
            "📶  Connected to AuroraNet.",
        ]
        tip = tk.Toplevel(self.root)
        tip.wm_overrideredirect(True)
        tip.configure(bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        tk.Label(tip, text="Notification Center", font=("Segoe UI", 10, "bold"),
                 bg=PANEL, fg=TEXT_BRIGHT, padx=16, pady=10).pack(anchor="w")
        for m in msgs:
            f = tk.Frame(tip, bg=PANEL2)
            f.pack(fill=tk.X, padx=10, pady=2)
            tk.Label(f, text=m, font=FONT_SM, bg=PANEL2, fg=TEXT,
                     padx=12, pady=8, anchor="w").pack(fill=tk.X)
        tk.Button(tip, text="Dismiss", font=FONT_SM, bg=PANEL, fg=ACCENT,
                  activebackground=PANEL2, bd=0, padx=12, pady=6,
                  cursor="hand2", command=tip.destroy).pack(pady=8)
        x = self.root.winfo_rootx() + self.root.winfo_width() - 280
        y = self.root.winfo_rooty() + self.root.winfo_height() - 250
        tip.geometry(f"260x{30 + len(msgs)*44 + 50}+{x}+{y}")
        tip.bind("<FocusOut>", lambda e: tip.destroy())
        tip.focus_set()

    # ── Start Menu ────────────────────────────────────────────────────────────
    def _toggle_start_menu(self):
        if hasattr(self, "_start_menu") and self._start_menu.winfo_exists():
            self._start_menu.destroy()
            return
        menu = tk.Toplevel(self.root)
        menu.wm_overrideredirect(True)
        menu.configure(bg=PANEL, highlightbackground=BORDER,
                       highlightthickness=1)
        self._start_menu = menu

        # Search bar
        sf = tk.Frame(menu, bg=PANEL)
        sf.pack(fill=tk.X, padx=12, pady=(12, 8))
        tk.Label(sf, text="🔍", font=("Segoe UI Emoji", 12), bg=PANEL,
                 fg=TEXT_DIM).pack(side=tk.LEFT)
        se = tk.Entry(sf, font=FONT, bg=PANEL2, fg=TEXT, bd=0,
                      insertbackground=ACCENT, width=24)
        se.pack(side=tk.LEFT, padx=6, ipady=6, fill=tk.X, expand=True)
        se.focus_set()

        # App grid
        tk.Label(menu, text="Pinned", font=("Segoe UI", 9, "bold"),
                 bg=PANEL, fg=TEXT_DIM, anchor="w").pack(fill=tk.X,
                 padx=14, pady=(4, 2))

        grid = tk.Frame(menu, bg=PANEL)
        grid.pack(padx=10, pady=4)

        all_apps = [
            ("📁", "Files",      self.open_files),
            ("📝", "Notes",      self.open_notes),
            ("⚡", "Terminal",   self.open_terminal),
            ("🔢", "Calculator", self.open_calculator),
            ("⚙️", "Settings",   self.open_settings),
            ("📊", "Monitor",    self.open_monitor),
        ]
        for i, (ico, name, cmd) in enumerate(all_apps):
            r, c = divmod(i, 4)
            cell = tk.Frame(grid, bg=PANEL, width=80, height=72,
                            cursor="hand2")
            cell.grid(row=r, column=c, padx=4, pady=4)
            cell.pack_propagate(False)
            tk.Label(cell, text=ico, font=("Segoe UI Emoji", 20),
                     bg=PANEL, fg=TEXT).pack(pady=(10, 2))
            tk.Label(cell, text=name, font=FONT_SM, bg=PANEL,
                     fg=TEXT, width=8).pack()

            def _cmd(c=cmd):
                menu.destroy()
                c()
            cell.bind("<Button-1>", lambda e, c=_cmd: c())
            for w in cell.winfo_children():
                w.bind("<Button-1>", lambda e, c=_cmd: c())

            def on_enter(e, f=cell):
                f.configure(bg=PANEL2)
                for w in f.winfo_children(): w.configure(bg=PANEL2)
            def on_leave(e, f=cell):
                f.configure(bg=PANEL)
                for w in f.winfo_children(): w.configure(bg=PANEL)
            cell.bind("<Enter>", on_enter)
            cell.bind("<Leave>", on_leave)
            for w in cell.winfo_children():
                w.bind("<Enter>", on_enter)
                w.bind("<Leave>", on_leave)

        # Shutdown row
        sep = tk.Frame(menu, bg=BORDER, height=1)
        sep.pack(fill=tk.X, padx=10, pady=8)
        bot = tk.Frame(menu, bg=PANEL)
        bot.pack(fill=tk.X, padx=10, pady=(0, 10))
        tk.Label(bot, text="👤  Zoro", font=FONT_SM, bg=PANEL,
                 fg=TEXT).pack(side=tk.LEFT, padx=4)
        tk.Button(bot, text="⏻  Quit", font=FONT_SM, bg=PANEL,
                  fg=BTN_CLOSE, activebackground=PANEL2, bd=0,
                  padx=10, cursor="hand2",
                  command=self.root.quit).pack(side=tk.RIGHT)

        menu.geometry(f"360x320+{self.root.winfo_rootx()+8}+"
                      f"{self.root.winfo_rooty()+self.root.winfo_height()-376}")
        menu.bind("<FocusOut>", lambda e: menu.destroy())
        menu.focus_set()

    # ── Generic App Window Factory ────────────────────────────────────────────
    def _new_window(self, title, icon, w=640, h=460):
        win = tk.Toplevel(self.root)
        win.title(f"{icon} {title}")
        win.geometry(f"{w}x{h}+{100+random.randint(0,100)}+{60+random.randint(0,60)}")
        win.configure(bg=WIN_BG)

        # Custom title bar
        tb = tk.Frame(win, bg=TITLEBAR, height=38)
        tb.pack(fill=tk.X)
        tb.pack_propagate(False)

        tk.Label(tb, text=f"{icon}  {title}", font=("Segoe UI", 10, "bold"),
                 bg=TITLEBAR, fg=TEXT).pack(side=tk.LEFT, padx=12)

        for txt, bg, cmd in [("—", BTN_MIN, win.iconify),
                               ("⊡", BTN_MAX, lambda: None),
                               ("✕", BTN_CLOSE, win.destroy)]:
            tk.Button(tb, text=txt, font=("Segoe UI", 9, "bold"),
                      bg=TITLEBAR, fg=bg, activebackground=bg,
                      activeforeground="white", bd=0, padx=10, pady=6,
                      cursor="hand2", command=cmd).pack(side=tk.RIGHT)

        # Drag-to-move via title bar
        self._make_draggable(win, tb)

        content = tk.Frame(win, bg=WIN_BG)
        content.pack(fill=tk.BOTH, expand=True)
        return win, content

    def _make_draggable(self, win, handle):
        handle._dx = handle._dy = 0
        def start(e): handle._dx = e.x; handle._dy = e.y
        def drag(e):
            x = win.winfo_x() + e.x - handle._dx
            y = win.winfo_y() + e.y - handle._dy
            win.geometry(f"+{x}+{y}")
        for child in handle.winfo_children():
            child.bind("<Button-1>", start)
            child.bind("<B1-Motion>", drag)
        handle.bind("<Button-1>", start)
        handle.bind("<B1-Motion>", drag)

    # ── Apps ──────────────────────────────────────────────────────────────────

    def open_files(self):
        win, c = self._new_window("Files", "📁", 700, 480)
        entries = [
            ("📁", "Documents",     "Folder", "—",       "Today"),
            ("📁", "Downloads",     "Folder", "—",       "Yesterday"),
            ("📁", "Pictures",      "Folder", "—",       "3 days ago"),
            ("📄", "aurora_os.py",  "Python", "14 KB",   "Just now"),
            ("📄", "readme.md",     "Markdown","2 KB",   "1 hour ago"),
            ("🖼️", "wallpaper.jpg", "Image",  "3.2 MB",  "2 days ago"),
            ("📋", "system.log",    "Log",    "128 KB",  "5 min ago"),
        ]
        # Path bar
        pb = tk.Frame(c, bg=PANEL2, height=36)
        pb.pack(fill=tk.X)
        pb.pack_propagate(False)
        tk.Label(pb, text="🏠 Home", font=FONT_SM, bg=PANEL2,
                 fg=ACCENT, padx=12).pack(side=tk.LEFT, pady=8)

        # Columns header
        cols = ("Name", "Type", "Size", "Modified")
        tree = ttk.Treeview(c, columns=cols, show="headings",
                            selectmode="browse")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=WIN_BG, foreground=TEXT,
                        fieldbackground=WIN_BG, bordercolor=BORDER,
                        rowheight=28, font=FONT_SM)
        style.configure("Treeview.Heading", background=PANEL2,
                        foreground=TEXT_DIM, font=("Segoe UI", 9, "bold"),
                        bordercolor=BORDER)
        style.map("Treeview", background=[("selected", PANEL2)],
                  foreground=[("selected", ACCENT)])

        widths = [260, 80, 80, 120]
        for col, wid in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=wid, anchor="w")

        for ico, name, ftype, size, mod in entries:
            tree.insert("", "end", values=(f"{ico}  {name}", ftype, size, mod))

        sb = tk.Scrollbar(c, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True, padx=1)

    def open_notes(self):
        win, c = self._new_window("Notes", "📝", 560, 480)
        self._notes_data = getattr(self, "_notes_data",
            "Welcome to Notes!\n\nStart typing your ideas here...\n")

        toolbar = tk.Frame(c, bg=PANEL2, height=36)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)
        for lbl in ["New", "Save", "Clear"]:
            tk.Button(toolbar, text=lbl, font=FONT_SM, bg=PANEL2,
                      fg=ACCENT, activebackground=PANEL,
                      bd=0, padx=10, cursor="hand2").pack(
                      side=tk.LEFT, pady=6, padx=2)

        count_var = tk.StringVar(value="0 words")
        tk.Label(toolbar, textvariable=count_var, font=FONT_SM,
                 bg=PANEL2, fg=TEXT_DIM).pack(side=tk.RIGHT, padx=10)

        ta = scrolledtext.ScrolledText(
            c, font=("Segoe UI", 11), bg=WIN_BG, fg=TEXT,
            insertbackground=ACCENT, bd=0, padx=16, pady=12,
            wrap=tk.WORD, selectbackground=PANEL2,
            selectforeground=ACCENT)
        ta.pack(fill=tk.BOTH, expand=True)
        ta.insert("1.0", self._notes_data)

        def update_count(e=None):
            txt = ta.get("1.0", "end-1c")
            self._notes_data = txt
            words = len(txt.split()) if txt.strip() else 0
            count_var.set(f"{words} word{'s' if words!=1 else ''}")
        ta.bind("<KeyRelease>", update_count)
        update_count()

    def open_terminal(self):
        win, c = self._new_window("Terminal", "⚡", 700, 440)
        hist = []
        hist_idx = [0]

        out = scrolledtext.ScrolledText(
            c, font=FONT_MONO, bg="#050a12", fg="#22d3ee",
            insertbackground="#22d3ee", bd=0, padx=10, pady=8,
            state="disabled", selectbackground="#1e3a5f")
        out.pack(fill=tk.BOTH, expand=True)

        def write(text, tag=None):
            out.configure(state="normal")
            out.insert("end", text)
            if tag:
                start = out.index(f"end - {len(text)+1}c")
                out.tag_add(tag, start, "end-1c")
            out.see("end")
            out.configure(state="disabled")

        out.tag_config("prompt", foreground="#4facfe")
        out.tag_config("error",  foreground="#ef4444")
        out.tag_config("ok",     foreground="#22d3ee")

        write("AuroraOS Terminal v1.0\n", "ok")
        write("Type 'help' for available commands.\n\n")

        inp_frame = tk.Frame(c, bg="#050a12")
        inp_frame.pack(fill=tk.X)
        tk.Label(inp_frame, text="aurora:~$ ", font=FONT_MONO,
                 bg="#050a12", fg="#4facfe").pack(side=tk.LEFT, padx=(10,0))
        inp = tk.Entry(inp_frame, font=FONT_MONO, bg="#050a12",
                       fg="#22d3ee", insertbackground="#22d3ee",
                       bd=0, relief="flat")
        inp.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0,10))
        inp.focus_set()

        COMMANDS = {
            "help":    lambda a: "\n".join([
                "  help      - show this help",
                "  ls        - list files",
                "  pwd       - print working directory",
                "  echo ...  - print arguments",
                "  date      - show current date/time",
                "  whoami    - current user",
                "  clear     - clear terminal",
                "  uname     - system info",
                "  uptime    - system uptime",
            ]),
            "ls":      lambda a: "Documents/  Downloads/  Pictures/  aurora_os.py  readme.md",
            "pwd":     lambda a: "/home/zoro",
            "whoami":  lambda a: "zoro",
            "date":    lambda a: datetime.datetime.now().strftime("%c"),
            "uname":   lambda a: "AuroraOS 1.0.0 (Browser Edition) x86_64",
            "uptime":  lambda a: f"up {random.randint(1,8)}h {random.randint(0,59)}m  load: {random.uniform(0.1,1.2):.2f}",
            "echo":    lambda a: " ".join(a),
        }

        start_time = time.time()

        def run(e=None):
            cmd_line = inp.get().strip()
            inp.delete(0, "end")
            if not cmd_line:
                return
            hist.append(cmd_line)
            hist_idx[0] = len(hist)
            write(f"aurora:~$ {cmd_line}\n", "prompt")
            parts = cmd_line.split()
            cmd, args = parts[0], parts[1:]
            if cmd == "clear":
                out.configure(state="normal")
                out.delete("1.0", "end")
                out.configure(state="disabled")
            elif cmd in COMMANDS:
                result = COMMANDS[cmd](args)
                write(result + "\n")
            else:
                write(f"bash: {cmd}: command not found\n", "error")
            write("\n")

        def history_up(e):
            if hist and hist_idx[0] > 0:
                hist_idx[0] -= 1
                inp.delete(0, "end")
                inp.insert(0, hist[hist_idx[0]])
        def history_down(e):
            if hist_idx[0] < len(hist) - 1:
                hist_idx[0] += 1
                inp.delete(0, "end")
                inp.insert(0, hist[hist_idx[0]])
            else:
                hist_idx[0] = len(hist)
                inp.delete(0, "end")

        inp.bind("<Return>", run)
        inp.bind("<Up>",     history_up)
        inp.bind("<Down>",   history_down)

    def open_calculator(self):
        win, c = self._new_window("Calculator", "🔢", 320, 480)
        expr = tk.StringVar(value="0")
        history_var = tk.StringVar(value="")
        _expr = [""]

        display = tk.Frame(c, bg=PANEL2)
        display.pack(fill=tk.X, padx=2, pady=2)
        tk.Label(display, textvariable=history_var, font=("Segoe UI", 9),
                 bg=PANEL2, fg=TEXT_DIM, anchor="e", height=1).pack(
                 fill=tk.X, padx=12, pady=(8,0))
        tk.Label(display, textvariable=expr, font=("Segoe UI", 28, "bold"),
                 bg=PANEL2, fg=TEXT_BRIGHT, anchor="e").pack(
                 fill=tk.X, padx=12, pady=(0,12))

        def press(val):
            cur = _expr[0]
            if val == "C":
                _expr[0] = ""
                expr.set("0")
                history_var.set("")
            elif val == "⌫":
                _expr[0] = cur[:-1]
                expr.set(_expr[0] or "0")
            elif val == "=":
                try:
                    result = eval(_expr[0].replace("×","*").replace("÷","/").replace("−","-"))
                    result = int(result) if isinstance(result, float) and result.is_integer() else round(result, 10)
                    history_var.set(_expr[0] + " =")
                    _expr[0] = str(result)
                    expr.set(str(result))
                except:
                    expr.set("Error")
                    _expr[0] = ""
            elif val == "%":
                try:
                    v = float(eval(_expr[0] or "0"))
                    _expr[0] = str(v / 100)
                    expr.set(_expr[0])
                except:
                    pass
            elif val == "+/−":
                try:
                    v = float(eval(_expr[0] or "0"))
                    _expr[0] = str(-v)
                    expr.set(_expr[0])
                except:
                    pass
            else:
                if _expr[0] == "Error":
                    _expr[0] = ""
                _expr[0] += val
                expr.set(_expr[0])

        buttons = [
            [("C", PANEL, TEXT_DIM), ("+/−", PANEL, TEXT_DIM), ("%", PANEL, TEXT_DIM), ("÷", PANEL2, ACCENT)],
            [("7", WIN_BG, TEXT),   ("8", WIN_BG, TEXT),   ("9", WIN_BG, TEXT),   ("×", PANEL2, ACCENT)],
            [("4", WIN_BG, TEXT),   ("5", WIN_BG, TEXT),   ("6", WIN_BG, TEXT),   ("−", PANEL2, ACCENT)],
            [("1", WIN_BG, TEXT),   ("2", WIN_BG, TEXT),   ("3", WIN_BG, TEXT),   ("+", PANEL2, ACCENT)],
            [("⌫", WIN_BG, TEXT),  ("0", WIN_BG, TEXT),   (".", WIN_BG, TEXT),   ("=", ACCENT, "#000")],
        ]
        for row in buttons:
            row_f = tk.Frame(c, bg=WIN_BG)
            row_f.pack(fill=tk.X, expand=True)
            for lbl, bg, fg in row:
                b = tk.Button(row_f, text=lbl,
                              font=("Segoe UI", 14),
                              bg=bg, fg=fg, activebackground=PANEL2,
                              activeforeground=TEXT_BRIGHT,
                              bd=0, padx=0, pady=0,
                              relief="flat", cursor="hand2",
                              command=lambda v=lbl: press(v))
                b.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                       padx=2, pady=2, ipady=10)

    def open_settings(self):
        win, c = self._new_window("Settings", "⚙️", 620, 480)

        sidebar = tk.Frame(c, bg=PANEL, width=160)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        main = tk.Frame(c, bg=WIN_BG)
        main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sections = [
            ("🎨", "Appearance"),
            ("🔊", "Sound"),
            ("🌐", "Network"),
            ("🔒", "Privacy"),
            ("⚡", "Power"),
            ("ℹ️", "About"),
        ]

        content_frames = {}

        def show_section(name):
            for f in content_frames.values():
                f.pack_forget()
            if name in content_frames:
                content_frames[name].pack(fill=tk.BOTH, expand=True,
                                          padx=20, pady=20)

        # Build content panes
        def make_about():
            f = tk.Frame(main, bg=WIN_BG)
            tk.Label(f, text="AuroraOS", font=("Segoe UI", 22, "bold"),
                     bg=WIN_BG, fg=TEXT_BRIGHT).pack(anchor="w", pady=(0,4))
            tk.Label(f, text="Version 1.0.0 MVP  •  Python/Tkinter",
                     font=FONT_SM, bg=WIN_BG, fg=TEXT_DIM).pack(anchor="w")
            tk.Frame(f, bg=BORDER, height=1).pack(fill=tk.X, pady=12)
            for k, v in [("Kernel", "TkAurora 6.3.0"),
                          ("Architecture", "x86_64"),
                          ("Python", "3.11+"),
                          ("Memory", f"{random.randint(3,6)} GB / 16 GB"),
                          ("CPU", "Aurora Core i7 (simulated)")]:
                row = tk.Frame(f, bg=WIN_BG)
                row.pack(fill=tk.X, pady=3)
                tk.Label(row, text=k, font=FONT_SM, bg=WIN_BG,
                         fg=TEXT_DIM, width=14, anchor="w").pack(side=tk.LEFT)
                tk.Label(row, text=v, font=FONT_SM, bg=WIN_BG,
                         fg=TEXT).pack(side=tk.LEFT)
            return f

        def make_appearance():
            f = tk.Frame(main, bg=WIN_BG)
            tk.Label(f, text="Appearance", font=FONT_LG,
                     bg=WIN_BG, fg=TEXT_BRIGHT).pack(anchor="w", pady=(0,12))
            for label, var_default in [
                ("Dark Mode", True),
                ("Transparency Effects", True),
                ("Animations", True),
                ("Show desktop icons", True),
            ]:
                row = tk.Frame(f, bg=WIN_BG)
                row.pack(fill=tk.X, pady=5)
                tk.Label(row, text=label, font=FONT,
                         bg=WIN_BG, fg=TEXT).pack(side=tk.LEFT)
                var = tk.BooleanVar(value=var_default)
                tk.Checkbutton(row, variable=var, bg=WIN_BG,
                               activebackground=WIN_BG,
                               selectcolor=PANEL2,
                               fg=ACCENT).pack(side=tk.RIGHT)
            tk.Label(f, text="Accent Color", font=FONT,
                     bg=WIN_BG, fg=TEXT_DIM).pack(anchor="w", pady=(12,4))
            colors_f = tk.Frame(f, bg=WIN_BG)
            colors_f.pack(anchor="w")
            for col in ["#4facfe", "#a78bfa", "#34d399", "#f472b6", "#fb923c"]:
                tk.Label(colors_f, bg=col, width=3, height=1,
                         relief="flat", cursor="hand2").pack(
                         side=tk.LEFT, padx=4, pady=2)
            return f

        content_frames["About"] = make_about()
        content_frames["Appearance"] = make_appearance()

        # Sidebar buttons
        for ico, name in sections:
            b = tk.Button(sidebar, text=f"{ico}  {name}",
                          font=FONT_SM, bg=PANEL, fg=TEXT,
                          activebackground=PANEL2, activeforeground=ACCENT,
                          bd=0, anchor="w", padx=14, pady=9, cursor="hand2",
                          command=lambda n=name: show_section(n))
            b.pack(fill=tk.X)

        show_section("About")

    def open_monitor(self):
        win, c = self._new_window("System Monitor", "📊", 560, 440)

        stats = {
            "CPU":    [random.randint(10, 80) for _ in range(30)],
            "RAM":    [random.randint(40, 70) for _ in range(30)],
            "Net ↑":  [random.randint(0,  20) for _ in range(30)],
        }

        # Summary cards
        cards = tk.Frame(c, bg=WIN_BG)
        cards.pack(fill=tk.X, padx=12, pady=10)
        card_labels = {}
        for name, color in [("CPU", ACCENT), ("RAM", ACCENT2),
                             ("Net ↑", "#34d399"), ("Disk", "#fb923c")]:
            cf = tk.Frame(cards, bg=PANEL2, width=110, height=68)
            cf.pack(side=tk.LEFT, padx=4)
            cf.pack_propagate(False)
            tk.Label(cf, text=name, font=FONT_SM, bg=PANEL2,
                     fg=TEXT_DIM).pack(pady=(8,0))
            v = tk.StringVar(value="—")
            tk.Label(cf, textvariable=v, font=("Segoe UI", 16, "bold"),
                     bg=PANEL2, fg=color).pack()
            card_labels[name] = v

        # Canvas chart
        chart = tk.Canvas(c, bg=PANEL2, height=220, highlightthickness=0)
        chart.pack(fill=tk.X, padx=12, pady=(0,8))

        colors = {"CPU": ACCENT, "RAM": ACCENT2, "Net ↑": "#34d399"}

        def draw_chart():
            chart.delete("all")
            cw = chart.winfo_width() or 520
            ch = 220
            pad = 32
            # Grid lines
            for i in range(5):
                y = pad + (ch - 2*pad) * i // 4
                chart.create_line(pad, y, cw-pad, y,
                                  fill=BORDER, width=1)
                chart.create_text(pad-4, y, text=f"{100-i*25}%",
                                  anchor="e", font=("Segoe UI", 7),
                                  fill=TEXT_DIM)
            # Lines
            for key, vals in stats.items():
                n = len(vals)
                pts = []
                for i, v in enumerate(vals):
                    x = pad + (cw - 2*pad) * i / (n-1)
                    y = pad + (ch - 2*pad) * (1 - v/100)
                    pts.extend([x, y])
                if len(pts) >= 4:
                    chart.create_line(*pts, fill=colors[key],
                                      width=2, smooth=True)
            # Legend
            lx = pad
            for key, col in colors.items():
                chart.create_rectangle(lx, ch-14, lx+12, ch-4,
                                       fill=col, outline="")
                chart.create_text(lx+16, ch-9, text=key,
                                  anchor="w", font=("Segoe UI", 8),
                                  fill=TEXT_DIM)
                lx += 70

        def update():
            if not win.winfo_exists():
                return
            cpu = random.randint(10, 85)
            ram = random.randint(42, 72)
            net = random.randint(0, 25)
            disk = random.randint(1, 15)
            stats["CPU"].append(cpu);   stats["CPU"].pop(0)
            stats["RAM"].append(ram);   stats["RAM"].pop(0)
            stats["Net ↑"].append(net); stats["Net ↑"].pop(0)
            card_labels["CPU"].set(f"{cpu}%")
            card_labels["RAM"].set(f"{ram}%")
            card_labels["Net ↑"].set(f"{net} MB/s")
            card_labels["Disk"].set(f"{disk}%")
            draw_chart()
            win.after(1500, update)

        c.after(200, update)

        # Process list
        tk.Label(c, text="Processes", font=("Segoe UI", 9, "bold"),
                 bg=WIN_BG, fg=TEXT_DIM).pack(anchor="w", padx=14)
        procs = [
            ("aurora_os.py",   "python",   f"{random.randint(80,200)} MB"),
            ("AuroraOS Shell", "system",   "48 MB"),
            ("FileSystem",     "service",  "12 MB"),
            ("NetworkMgr",     "service",  "8 MB"),
        ]
        for name, ptype, mem in procs:
            row = tk.Frame(c, bg=WIN_BG)
            row.pack(fill=tk.X, padx=14, pady=1)
            tk.Label(row, text=name, font=FONT_SM, bg=WIN_BG,
                     fg=TEXT, width=20, anchor="w").pack(side=tk.LEFT)
            tk.Label(row, text=ptype, font=FONT_SM, bg=WIN_BG,
                     fg=TEXT_DIM, width=10).pack(side=tk.LEFT)
            tk.Label(row, text=mem, font=FONT_SM, bg=WIN_BG,
                     fg=ACCENT2, width=10, anchor="e").pack(side=tk.RIGHT)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    os = AuroraOS()
    os.run()
