"""
gui.py  —  Cosmo AI  ·  Modern Cosmic Edition  v4.0
─────────────────────────────────────────────────────
A premium ChatGPT-style Tkinter interface.

Classes
───────
  P               – every colour, font, and dimension constant
  TypingIndicator – animated dots while Cosmo thinks
  GamePanel       – interactive Q&A panel (replaces chat during games)
  CosmoGUI        – main window; owns the entire application lifecycle

Backend contract (unchanged)
─────────────────────────────
  bot.process_message(text)   → (response_str, session_ended)
  bot.session.start(game)     → opening_dict
  bot.session.answer(text)    → result_dict
  bot.teach_confirm(bool, str)→ reply_str
  TEACH_PROMPT constant       → signal that teach flow is needed
"""

import sys
import tkinter as tk
from tkinter import font as tkfont

sys.path.insert(0, ".")
from bot   import CosmoBot
from brain import TEACH_PROMPT
from games import BaseGame


# ══════════════════════════════════════════════════════════════════════════════
#  P  —  Palette  (single source of truth for every visual value)
# ══════════════════════════════════════════════════════════════════════════════
class P:
    # Window
    WIN_W, WIN_H     = 1020, 740
    MIN_W, MIN_H     = 780,  560

    # Deep-space backgrounds
    BG_ROOT          = "#080B14"   # root window — darkest layer
    BG_SIDEBAR       = "#0A0D18"   # left sidebar
    BG_CHAT          = "#0C0F1D"   # main chat canvas
    BG_HEADER        = "#09091A"   # top bar
    BG_INPUT_ZONE    = "#0C0F1D"   # footer zone background
    BG_INPUT_PILL    = "#141728"   # the rounded pill container
    BG_INPUT_FIELD   = "#141728"   # text entry background
    BG_USER_BUBBLE   = "#1B2B52"   # user message bubble
    BG_BOT_BUBBLE    = "#0F1426"   # cosmo message bubble
    BG_HOVER         = "#161C30"   # hover on sidebar items
    BG_ACTIVE        = "#1A2240"   # active / selected
    BG_DIALOG        = "#0C0F1D"
    BG_GAME          = "#0C0F1D"
    BG_GAME_HDR      = "#09091A"
    BG_SEPARATOR     = "#141728"

    # Accent palette (soft, not harsh neon)
    BLUE             = "#4F8EF0"   # primary blue
    BLUE_BRIGHT      = "#70AAFF"   # hover / focus
    VIOLET           = "#8B5CF6"   # violet
    VIOLET_BRIGHT    = "#A78BFA"
    CYAN             = "#22C4E0"   # soft cyan
    PINK             = "#D946A8"   # soft pink
    GREEN            = "#10B981"   # success
    GREEN_DIM        = "#0A5C47"   # dimmed status
    AMBER            = "#F59E0B"   # warning

    # Text hierarchy
    TXT_H1           = "#F0F4FF"   # titles
    TXT_BODY         = "#C8D0E8"   # main body text
    TXT_DIM          = "#60698A"   # timestamps, hints
    TXT_GHOST        = "#32374F"   # disabled / placeholder
    TXT_USER         = "#D4E2FF"   # user bubble text
    TXT_BOT          = "#BFC8E8"   # bot bubble text
    TXT_LABEL        = "#7C86B0"   # small labels

    # Border / divider
    BORDER           = "#1A1F36"
    BORDER_FOCUS     = "#4F8EF0"
    BORDER_PILL      = "#1E2440"

    # Send button
    BTN_BG           = "#4F8EF0"
    BTN_HOVER        = "#70AAFF"
    BTN_DISABLED     = "#1E2A42"

    # Game feedback
    GAME_OK          = "#10B981"
    GAME_FAIL        = "#D946A8"
    GAME_SCORE       = "#8B5CF6"
    GAME_PROMPT      = "#22C4E0"

    # Scrollbar
    SCROLL_BG        = "#0C0F1D"
    SCROLL_FG        = "#1E2748"

    # Fonts
    FONT             = "Segoe UI"

    # Layout
    SIDEBAR_W        = 64          # icon-only sidebar width
    CHAT_MAX_W       = 740         # max width of centered chat column
    BUBBLE_V_PAD     = 14          # vertical padding inside bubbles
    BUBBLE_H_PAD     = 20          # horizontal padding inside bubbles
    HEADER_H         = 58
    INPUT_ZONE_H     = 100


# ══════════════════════════════════════════════════════════════════════════════
#  TypingIndicator
# ══════════════════════════════════════════════════════════════════════════════
class TypingIndicator:
    """
    Inserts a smooth animated three-dot indicator into the chat widget
    while Cosmo is processing.  Removed cleanly when the response arrives.
    """

    _FRAMES = ["   ·  ·  ·  ", "   ●  ·  ·  ", "   ●  ●  ·  ", "   ●  ●  ●  "]

    def __init__(self, chat: tk.Text) -> None:
        self._chat  = chat
        self._frame = 0
        self._job   = None
        self._mark  = None

    def show(self) -> None:
        self._chat.config(state=tk.NORMAL)
        self._chat.insert(tk.END, "\n", "v_gap")
        self._chat.insert(tk.END, "  Cosmo\n", "bot_label")
        self._mark = self._chat.index(tk.END + " -1c linestart")
        self._chat.insert(tk.END, self._FRAMES[0] + "\n", "typing")
        self._chat.config(state=tk.DISABLED)
        self._chat.see(tk.END)
        self._tick()

    def _tick(self) -> None:
        self._frame = (self._frame + 1) % len(self._FRAMES)
        self._chat.config(state=tk.NORMAL)
        try:
            end = self._chat.index(f"{self._mark} lineend")
            self._chat.delete(self._mark, end)
            self._chat.insert(self._mark, self._FRAMES[self._frame], "typing")
        except tk.TclError:
            pass
        self._chat.config(state=tk.DISABLED)
        self._job = self._chat.after(380, self._tick)

    def hide(self) -> None:
        if self._job:
            self._chat.after_cancel(self._job)
            self._job = None
        self._chat.config(state=tk.NORMAL)
        try:
            if self._mark:
                s = self._chat.index(f"{self._mark} -2l linestart")
                e = self._chat.index(f"{self._mark} +1l lineend +1c")
                self._chat.delete(s, e)
        except tk.TclError:
            pass
        self._chat.config(state=tk.DISABLED)
        self._mark = None


# ══════════════════════════════════════════════════════════════════════════════
#  GamePanel
# ══════════════════════════════════════════════════════════════════════════════
class GamePanel(tk.Frame):
    """
    Replaces the chat area while a mini-game is active.
    Communicates with the backend exclusively through
    bot.session.start() and bot.session.answer().
    Uses grid layout internally to keep input always visible.
    """

    def __init__(self, parent: tk.Widget, bot: CosmoBot, on_close) -> None:
        super().__init__(parent, bg=P.BG_GAME)
        self._bot      = bot
        self._on_close = on_close
        self._build()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build(self) -> None:
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Row 0 — header bar
        hdr = tk.Frame(self, bg=P.BG_GAME_HDR, height=54)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.pack_propagate(False)

        self._title_lbl = tk.Label(
            hdr, text="🎮  Game Zone",
            bg=P.BG_GAME_HDR, fg=P.CYAN,
            font=(P.FONT, 13, "bold"),
        )
        self._title_lbl.pack(side=tk.LEFT, padx=28, pady=14)

        back = tk.Button(
            hdr, text="← Back to Chat",
            bg=P.BG_GAME_HDR, fg=P.TXT_DIM,
            font=(P.FONT, 10), bd=0, cursor="hand2",
            activebackground=P.BG_GAME_HDR, activeforeground=P.TXT_BODY,
            command=self._close,
        )
        back.pack(side=tk.RIGHT, padx=24)
        back.bind("<Enter>", lambda e: back.config(fg=P.PINK))
        back.bind("<Leave>", lambda e: back.config(fg=P.TXT_DIM))

        # Row 1 — thin accent line
        tk.Frame(self, bg=P.VIOLET, height=1).grid(row=1, column=0, sticky="ew")

        # Row 2 — scrollable game display
        wrap = tk.Frame(self, bg=P.BG_GAME)
        wrap.grid(row=2, column=0, sticky="nsew", padx=80, pady=(20, 8))
        wrap.grid_rowconfigure(0, weight=1)
        wrap.grid_columnconfigure(0, weight=1)

        sb = tk.Scrollbar(
            wrap, bg=P.SCROLL_BG, troughcolor=P.SCROLL_BG,
            activebackground=P.VIOLET, width=5,
        )
        sb.grid(row=0, column=1, sticky="ns")

        self._display = tk.Text(
            wrap,
            bg=P.BG_GAME, fg=P.TXT_BOT,
            font=(P.FONT, 12),
            bd=0, relief=tk.FLAT, wrap=tk.WORD,
            state=tk.DISABLED,
            padx=8, pady=12,
            cursor="arrow",
            selectbackground=P.BG_USER_BUBBLE,
            spacing1=4, spacing3=4,
            yscrollcommand=sb.set,
        )
        self._display.grid(row=0, column=0, sticky="nsew")
        sb.config(command=self._display.yview)
        self._config_tags()

        # Row 3 — answer input (always visible via grid)
        self._input_row = tk.Frame(self, bg=P.BG_GAME)
        self._input_row.grid(row=3, column=0, sticky="ew", padx=80, pady=(0, 20))
        self._input_row.grid_columnconfigure(0, weight=1)

        self._ans_var = tk.StringVar()
        self._ans_entry = tk.Entry(
            self._input_row,
            textvariable=self._ans_var,
            bg=P.BG_INPUT_PILL, fg=P.TXT_BODY,
            insertbackground=P.CYAN,
            font=(P.FONT, 13),
            bd=0, relief=tk.FLAT,
            highlightthickness=1,
            highlightcolor=P.VIOLET,
            highlightbackground=P.BORDER_PILL,
        )
        self._ans_entry.grid(row=0, column=0, sticky="ew", ipady=13, padx=(0, 10))
        self._ans_entry.bind("<Return>", self._submit)

        self._sub_btn = tk.Button(
            self._input_row,
            text="Submit  ↵",
            bg=P.BTN_BG, fg="white",
            font=(P.FONT, 11, "bold"),
            bd=0, relief=tk.FLAT, cursor="hand2",
            padx=20, pady=10,
            activebackground=P.BTN_HOVER,
            command=self._submit,
        )
        self._sub_btn.grid(row=0, column=1)
        self._sub_btn.bind("<Enter>", lambda e: self._sub_btn.config(bg=P.BTN_HOVER))
        self._sub_btn.bind("<Leave>", lambda e: self._sub_btn.config(bg=P.BTN_BG))

        # Row 4 — return button (hidden until game ends)
        self._ret_btn = tk.Button(
            self,
            text="✦  Return to Chat",
            bg=P.VIOLET, fg="white",
            font=(P.FONT, 12, "bold"),
            bd=0, relief=tk.FLAT, cursor="hand2",
            padx=28, pady=12,
            activebackground=P.BLUE,
            command=self._close,
        )

    def _config_tags(self) -> None:
        d = self._display
        d.tag_config("label",   foreground=P.VIOLET,      font=(P.FONT, 9,  "bold"))
        d.tag_config("msg",     foreground=P.TXT_BOT,     font=(P.FONT, 12))
        d.tag_config("prompt",  foreground=P.GAME_PROMPT, font=(P.FONT, 13, "bold"))
        d.tag_config("you",     foreground=P.BLUE_BRIGHT, font=(P.FONT, 12, "bold"))
        d.tag_config("correct", foreground=P.GAME_OK,     font=(P.FONT, 12, "bold"))
        d.tag_config("wrong",   foreground=P.GAME_FAIL,   font=(P.FONT, 12, "bold"))
        d.tag_config("score",   foreground=P.GAME_SCORE,  font=(P.FONT, 13, "bold"))
        d.tag_config("gap",     font=(P.FONT, 4))

    # ── Public ────────────────────────────────────────────────────────────────
    def launch(self, game: BaseGame) -> None:
        self._bot.session.cancel()
        opening = self._bot.session.start(game)
        self._title_lbl.config(text=f"🎮  {game.name}")
        self._ret_btn.grid_remove()
        self._input_row.grid(row=3, column=0, sticky="ew", padx=80, pady=(0, 20))
        self._ans_entry.config(state=tk.NORMAL)
        self._sub_btn.config(state=tk.NORMAL)
        self._ans_var.set("")
        self._clear()
        self._put("label", "  Cosmo\n")
        self._put("msg",   "  " + opening["message"] + "\n\n")
        for line in opening.get("prompt", "").split("\n"):
            if line.strip():
                self._put("prompt", "  " + line + "\n")
        self.after(80, self._ans_entry.focus_set)

    # ── Private ───────────────────────────────────────────────────────────────
    def _submit(self, _=None) -> None:
        text = self._ans_var.get().strip()
        if not text:
            return
        self._ans_var.set("")
        self._put("gap", "\n")
        self._put("you", f"  You:  {text}\n")

        result = self._bot.session.answer(text)
        msg    = result["message"]

        self._put("gap", "\n")
        for line in msg.split("\n"):
            if not line.strip():
                self._put("gap", "\n")
                continue
            if any(k in line for k in ("Final Score", "🎯", "🏆", "🌟", "👍", "📚")):
                self._put("score",   "  " + line + "\n")
            elif "\u2705" in line:
                self._put("correct", "  " + line + "\n")
            elif "\u274c" in line or "\u26a0\ufe0f" in line:
                self._put("wrong",   "  " + line + "\n")
            else:
                self._put("msg",     "  " + line + "\n")

        if result.get("done"):
            self._finish()
        else:
            if result.get("prompt"):
                self._put("gap", "\n")
                for line in result["prompt"].split("\n"):
                    if line.strip():
                        self._put("prompt", "  " + line + "\n")
            self.after(10, self._ans_entry.focus_set)

    def _finish(self) -> None:
        self._ans_entry.config(state=tk.DISABLED)
        self._sub_btn.config(state=tk.DISABLED)
        self._input_row.grid_remove()
        self._ret_btn.grid(row=4, column=0, pady=(4, 28))
        self.after(60, self._ret_btn.focus_set)

    def _close(self) -> None:
        self._bot.session.cancel()
        self._on_close()

    def _clear(self) -> None:
        self._display.config(state=tk.NORMAL)
        self._display.delete("1.0", tk.END)
        self._display.config(state=tk.DISABLED)

    def _put(self, tag: str, text: str) -> None:
        self._display.config(state=tk.NORMAL)
        self._display.insert(tk.END, text, tag)
        self._display.config(state=tk.DISABLED)
        self._display.see(tk.END)


# ══════════════════════════════════════════════════════════════════════════════
#  CosmoGUI  —  main application window
# ══════════════════════════════════════════════════════════════════════════════
class CosmoGUI:
    """
    Main Tkinter window.

    Window layout (left sidebar + main column):
    ┌──────┬─────────────────────────────────────┐
    │      │  Header  (title · status · timer)   │
    │ Side │─────────────────────────────────────│
    │ bar  │  Chat area  (centered, scrollable)  │
    │      │─────────────────────────────────────│
    │      │  Input zone  (floating pill)         │
    └──────┴─────────────────────────────────────┘
    """

    # ── Init ──────────────────────────────────────────────────────────────────
    def __init__(self) -> None:
        # Backend
        self._bot = CosmoBot()
        self._bot.boot()

        # Root window
        self._root = tk.Tk()
        self._root.title("Cosmo AI")
        self._root.configure(bg=P.BG_ROOT)
        self._root.minsize(P.MIN_W, P.MIN_H)
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        self._root.geometry(
            f"{P.WIN_W}x{P.WIN_H}+{(sw-P.WIN_W)//2}+{(sh-P.WIN_H)//2}"
        )

        # State
        self._teach_pending      = False
        self._session_seconds    = 0
        self._typing_indicator   = None
        self._game_panel_visible = False
        self._placeholder_active = True

        # Onboarding (before building UI so dialog appears centred)
        if self._bot.profile.is_new_user():
            name = self._onboard()
            self._bot.initialize_user(name or "Friend")
        self._bot.profile.load()
        self._bot.theme.load()

        # Build UI
        self._build_outer_shell()   # sidebar + right column via grid
        self._build_header()
        self._build_chat_area()
        self._build_input_zone()

        self._root.bind("<Configure>", self._on_resize)

        # Welcome message + focus
        name = self._bot.profile.name
        self._post_bot(
            f"Hey {name}! ✦  I'm Cosmo — your cosmic AI companion.\n"
            f"Chat naturally, or type  !help  to see what I can do."
        )
        self._start_timer()
        self._input_text.focus_set()

    # ── Outer shell: sidebar + right column ──────────────────────────────────
    def _build_outer_shell(self) -> None:
        # Root uses grid: col 0 = sidebar, col 1 = main column
        self._root.grid_columnconfigure(1, weight=1)
        self._root.grid_rowconfigure(0, weight=1)

        # ── Left sidebar ──────────────────────────────────────────
        self._sidebar = tk.Frame(
            self._root, bg=P.BG_SIDEBAR, width=P.SIDEBAR_W,
        )
        self._sidebar.grid(row=0, column=0, sticky="nsew")
        self._sidebar.grid_propagate(False)
        self._build_sidebar()

        # ── Right column (header + chat + input) ──────────────────
        self._col = tk.Frame(self._root, bg=P.BG_CHAT)
        self._col.grid(row=0, column=1, sticky="nsew")
        self._col.grid_rowconfigure(1, weight=1)   # chat row expands
        self._col.grid_columnconfigure(0, weight=1)

    def _build_sidebar(self) -> None:
        """Icon-only vertical sidebar with navigation buttons."""
        s = self._sidebar

        # Top: logo mark
        tk.Label(
            s, text="✦",
            bg=P.BG_SIDEBAR, fg=P.BLUE,
            font=(P.FONT, 18, "bold"),
        ).pack(pady=(18, 24))

        # Divider
        tk.Frame(s, bg=P.BORDER, height=1).pack(fill=tk.X, padx=12)

        # Nav buttons — purely visual, expand in future iterations
        nav_items = [
            ("💬", "Chat"),
            ("🎮", "Games"),
            ("📜", "History"),
            ("⚙️", "Settings"),
        ]
        for icon, tip in nav_items:
            btn = tk.Label(
                s, text=icon,
                bg=P.BG_SIDEBAR, fg=P.TXT_DIM,
                font=(P.FONT, 16),
                cursor="hand2",
                width=3, pady=10,
            )
            btn.pack(fill=tk.X, pady=2)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=P.BG_HOVER, fg=P.TXT_BODY))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=P.BG_SIDEBAR, fg=P.TXT_DIM))

        # Bottom: theme quick-cycle button
        tk.Frame(s, bg=P.BORDER, height=1).pack(fill=tk.X, padx=12, side=tk.BOTTOM, pady=(0, 8))
        theme_btn = tk.Label(
            s, text="🎨",
            bg=P.BG_SIDEBAR, fg=P.TXT_DIM,
            font=(P.FONT, 15),
            cursor="hand2",
            width=3, pady=10,
        )
        theme_btn.pack(side=tk.BOTTOM, pady=4)
        theme_btn.bind("<Button-1>", self._cycle_theme)
        theme_btn.bind("<Enter>", lambda e: theme_btn.config(bg=P.BG_HOVER, fg=P.VIOLET))
        theme_btn.bind("<Leave>", lambda e: theme_btn.config(bg=P.BG_SIDEBAR, fg=P.TXT_DIM))

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self) -> None:
        self._header = tk.Frame(
            self._col, bg=P.BG_HEADER, height=P.HEADER_H,
        )
        self._header.grid(row=0, column=0, sticky="ew")
        self._header.pack_propagate(False)

        # Left: pulsing dot + title
        left = tk.Frame(self._header, bg=P.BG_HEADER)
        left.pack(side=tk.LEFT, padx=28, anchor=tk.W)

        dot_cv = tk.Canvas(left, width=9, height=9,
                           bg=P.BG_HEADER, highlightthickness=0)
        dot_cv.pack(side=tk.LEFT, padx=(0, 10), pady=20)
        dot_cv.create_oval(1, 1, 8, 8, fill=P.GREEN, outline="")
        self._pulse_dot(dot_cv)

        tc = tk.Frame(left, bg=P.BG_HEADER)
        tc.pack(side=tk.LEFT)
        tk.Label(tc, text="Cosmo AI",
                 bg=P.BG_HEADER, fg=P.TXT_H1,
                 font=(P.FONT, 14, "bold")).pack(anchor=tk.W)
        tk.Label(tc, text="Your cosmic chat companion  ✦",
                 bg=P.BG_HEADER, fg=P.TXT_DIM,
                 font=(P.FONT, 8)).pack(anchor=tk.W)

        # Right: user chip + timer
        right = tk.Frame(self._header, bg=P.BG_HEADER)
        right.pack(side=tk.RIGHT, padx=24)

        self._user_lbl = tk.Label(
            right,
            text=f"  {self._bot.profile.name}  ",
            bg=P.BG_ACTIVE, fg=P.BLUE_BRIGHT,
            font=(P.FONT, 9, "bold"),
            padx=10, pady=4,
        )
        self._user_lbl.pack(anchor=tk.E, pady=(12, 2))

        self._timer_lbl = tk.Label(
            right, text="00:00",
            bg=P.BG_HEADER, fg=P.TXT_DIM,
            font=(P.FONT, 8),
        )
        self._timer_lbl.pack(anchor=tk.E)

        # Bottom hairline
        tk.Frame(self._col, bg=P.BORDER, height=1).grid(
            row=0, column=0, sticky="sew", pady=(P.HEADER_H - 1, 0)
        )

    # ── Chat area ─────────────────────────────────────────────────────────────
    def _build_chat_area(self) -> None:
        self._chat_frame = tk.Frame(self._col, bg=P.BG_CHAT)
        self._chat_frame.grid(row=1, column=0, sticky="nsew")

        self._chat_outer = tk.Frame(self._chat_frame, bg=P.BG_CHAT)
        self._chat_outer.pack(fill=tk.BOTH, expand=True)

        sb = tk.Scrollbar(
            self._chat_outer,
            bg=P.SCROLL_BG, troughcolor=P.SCROLL_BG,
            activebackground=P.VIOLET, width=5,
        )
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self._chat = tk.Text(
            self._chat_outer,
            bg=P.BG_CHAT, fg=P.TXT_BODY,
            font=(P.FONT, 12),
            bd=0, relief=tk.FLAT,
            wrap=tk.WORD,
            state=tk.DISABLED,
            cursor="arrow",
            selectbackground=P.BG_USER_BUBBLE,
            yscrollcommand=sb.set,
            spacing1=0, spacing3=0,
            padx=0, pady=0,
        )
        self._chat.pack(fill=tk.BOTH, expand=True)
        sb.config(command=self._chat.yview)
        self._setup_tags()

        # Game panel (hidden initially, same parent as chat_outer)
        self._game_panel = GamePanel(
            self._chat_frame, self._bot,
            on_close=self._close_game_panel,
        )

    def _setup_tags(self) -> None:
        c = self._chat
        c.tag_config("v_gap",    font=(P.FONT, 6))
        c.tag_config("h_gap",    font=(P.FONT, 10))
        c.tag_config("user_lbl",
            foreground=P.TXT_DIM,
            font=(P.FONT, 8),
            justify=tk.RIGHT,
        )
        c.tag_config("user_msg",
            background=P.BG_USER_BUBBLE,
            foreground=P.TXT_USER,
            font=(P.FONT, 12),
            justify=tk.RIGHT,
            spacing1=P.BUBBLE_V_PAD,
            spacing3=P.BUBBLE_V_PAD,
        )
        c.tag_config("bot_label",
            foreground=P.VIOLET,
            font=(P.FONT, 8, "bold"),
        )
        c.tag_config("bot_msg",
            background=P.BG_BOT_BUBBLE,
            foreground=P.TXT_BOT,
            font=(P.FONT, 12),
            spacing1=P.BUBBLE_V_PAD,
            spacing3=P.BUBBLE_V_PAD,
        )
        c.tag_config("system",
            foreground=P.TXT_DIM,
            font=(P.FONT, 9, "italic"),
            justify=tk.CENTER,
        )
        c.tag_config("typing",
            foreground=P.VIOLET,
            font=(P.FONT, 12),
        )
        self._root.after(60, self._apply_margins)

    def _apply_margins(self) -> None:
        """Keep chat content in a centered, max-width column."""
        w = self._chat.winfo_width()
        if w < 100:
            self._root.after(120, self._apply_margins)
            return
        col   = min(P.CHAT_MAX_W, w - 40)
        pad   = max(20, (w - col) // 2)
        right_extra = 100   # push user bubbles left of center

        self._chat.tag_config("user_msg",
            lmargin1=pad + right_extra, lmargin2=pad + right_extra,
            rmargin=pad)
        self._chat.tag_config("user_lbl",
            lmargin1=pad + right_extra, lmargin2=pad + right_extra,
            rmargin=pad)
        self._chat.tag_config("bot_msg",
            lmargin1=pad, lmargin2=pad,
            rmargin=pad + right_extra)
        self._chat.tag_config("bot_label",
            lmargin1=pad, lmargin2=pad,
            rmargin=pad + right_extra)
        self._chat.tag_config("system",
            lmargin1=pad, lmargin2=pad, rmargin=pad)

    # ── Input zone ────────────────────────────────────────────────────────────
    def _build_input_zone(self) -> None:
        # Hairline separator
        tk.Frame(self._col, bg=P.BORDER, height=1).grid(
            row=2, column=0, sticky="ew")

        # Footer background
        self._footer = tk.Frame(self._col, bg=P.BG_INPUT_ZONE)
        self._footer.grid(row=3, column=0, sticky="ew")

        # Outer centering wrapper
        self._input_wrap = tk.Frame(self._footer, bg=P.BG_INPUT_ZONE)
        self._input_wrap.pack(fill=tk.X, padx=0, pady=12)

        # Pill container — gives the rounded elevated look
        self._pill = tk.Frame(
            self._input_wrap,
            bg=P.BG_INPUT_PILL,
            highlightthickness=1,
            highlightbackground=P.BORDER_PILL,
            highlightcolor=P.BORDER_FOCUS,
        )
        self._pill.pack(fill=tk.X, padx=100)

        # Multiline text entry (Shift+Enter = newline, Enter = send)
        self._input_text = tk.Text(
            self._pill,
            bg=P.BG_INPUT_FIELD, fg=P.TXT_BODY,
            insertbackground=P.CYAN,
            font=(P.FONT, 13),
            bd=0, relief=tk.FLAT,
            wrap=tk.WORD,
            height=1,
            padx=18, pady=14,
        )
        self._input_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._input_text.bind("<Return>",       self._on_enter)
        self._input_text.bind("<Shift-Return>", self._on_shift_enter)
        self._input_text.bind("<KeyRelease>",   self._on_key_up)
        self._input_text.bind("<FocusIn>",      self._on_focus_in)
        self._input_text.bind("<FocusOut>",     self._on_focus_out)

        # Placeholder
        self._show_placeholder()

        # Send button
        self._send_btn = tk.Button(
            self._pill,
            text="⬆",
            font=(P.FONT, 15, "bold"),
            bg=P.BTN_BG, fg="white",
            activebackground=P.BTN_HOVER,
            bd=0, relief=tk.FLAT, cursor="hand2",
            padx=14, pady=10,
            command=self._on_send,
        )
        self._send_btn.pack(side=tk.RIGHT, padx=(4, 8), pady=6)
        self._send_btn.bind("<Enter>", lambda e: self._send_btn.config(bg=P.BTN_HOVER))
        self._send_btn.bind("<Leave>", lambda e: self._send_btn.config(bg=P.BTN_BG))

        # Hint label
        tk.Label(
            self._input_wrap,
            text="Enter  ·  send    Shift+Enter  ·  new line",
            bg=P.BG_INPUT_ZONE, fg=P.TXT_GHOST,
            font=(P.FONT, 7),
        ).pack(pady=(4, 2))

    # ── Placeholder ───────────────────────────────────────────────────────────
    def _show_placeholder(self) -> None:
        self._input_text.insert("1.0", "Message Cosmo...")
        self._input_text.config(fg=P.TXT_GHOST)
        self._placeholder_active = True

    def _hide_placeholder(self) -> None:
        if self._placeholder_active:
            self._input_text.delete("1.0", tk.END)
            self._input_text.config(fg=P.TXT_BODY)
            self._placeholder_active = False

    def _on_focus_in(self, _=None) -> None:
        self._hide_placeholder()
        self._pill.config(highlightbackground=P.BORDER_FOCUS)

    def _on_focus_out(self, _=None) -> None:
        self._pill.config(highlightbackground=P.BORDER_PILL)
        if not self._input_text.get("1.0", tk.END).strip():
            self._show_placeholder()

    # ── Input events ──────────────────────────────────────────────────────────
    def _on_enter(self, _=None) -> str:
        self._on_send()
        return "break"

    def _on_shift_enter(self, _=None) -> None:
        self._root.after(10, self._resize_input)

    def _on_key_up(self, _=None) -> None:
        if not self._placeholder_active:
            self._resize_input()

    def _resize_input(self) -> None:
        lines = int(self._input_text.index(tk.END).split(".")[0]) - 1
        self._input_text.config(height=max(1, min(lines, 5)))

    # ── Send / deliver ────────────────────────────────────────────────────────
    def _on_send(self, _=None) -> None:
        if self._placeholder_active:
            return
        text = self._input_text.get("1.0", tk.END).strip()
        if not text:
            return

        # Reset input widget
        self._input_text.delete("1.0", tk.END)
        self._input_text.config(height=1)
        self._show_placeholder()
        self._lock_input()

        # Post user bubble
        self._post_user(text)

        # Teach mode
        if self._teach_pending:
            self._teach_pending = False
            reply = (self._bot.teach_confirm(False)
                     if text.lower() in ("no", "n", "nope", "skip")
                     else self._bot.teach_confirm(True, text))
            self._post_bot(reply)
            self._unlock_input()
            return

        # GUI-intercepted commands (no typing delay)
        lt = text.strip().lower()
        if lt in ("!reset", "/reset"):
            self._handle_reset()
            return
        if lt in ("!clear", "/clear"):
            self._clear_chat()
            return
        if lt.startswith("!game") or lt.startswith("/game"):
            args = text.split(None, 1)[1].strip() if len(text.split()) > 1 else ""
            self._typing_then(lambda: self._handle_game(args))
            return

        # Normal flow
        self._typing_then(lambda: self._deliver(text))

    def _typing_then(self, cb) -> None:
        self._typing_indicator = TypingIndicator(self._chat)
        self._typing_indicator.show()
        self._root.after(900, cb)

    def _deliver(self, text: str) -> None:
        if self._typing_indicator:
            self._typing_indicator.hide()
            self._typing_indicator = None

        response, ended = self._bot.process_message(text)

        if ended:
            self._post_bot(response)
            self._post_system("Session ended  ·  restart Cosmo to continue")
            return

        if response == TEACH_PROMPT:
            self._teach_pending = True
            self._post_bot(
                "Hmm, I don't know that one yet. 🤔\n"
                "Want to teach me? Type your reply — or 'no' to skip."
            )
            self._unlock_input()
            return

        if response == "":
            self._handle_game("")
            return

        if response:
            self._post_bot(response)
            if "Theme changed" in response or "✨" in response:
                self._root.after(60, self._apply_theme)

        self._unlock_input()

    def _lock_input(self) -> None:
        self._input_text.config(state=tk.DISABLED)
        self._send_btn.config(state=tk.DISABLED, bg=P.BTN_DISABLED)

    def _unlock_input(self) -> None:
        self._input_text.config(state=tk.NORMAL)
        self._send_btn.config(state=tk.NORMAL, bg=P.BTN_BG)
        self._hide_placeholder()
        self._input_text.focus_set()

    # ── Message rendering ─────────────────────────────────────────────────────
    def _post_user(self, text: str) -> None:
        c = self._chat
        c.config(state=tk.NORMAL)
        c.insert(tk.END, "\n", "h_gap")
        c.insert(tk.END, "  You  \n", "user_lbl")
        padded = "\n".join(
            f"  {ln}  " for ln in text.split("\n")
        )
        c.insert(tk.END, padded + "\n", "user_msg")
        c.config(state=tk.DISABLED)
        c.see(tk.END)

    def _post_bot(self, text: str) -> None:
        c = self._chat
        c.config(state=tk.NORMAL)
        c.insert(tk.END, "\n", "h_gap")
        c.insert(tk.END, "  Cosmo  \n", "bot_label")
        padded = "\n".join(
            f"  {ln}  " for ln in text.split("\n")
        )
        c.insert(tk.END, padded + "\n", "bot_msg")
        c.config(state=tk.DISABLED)
        c.see(tk.END)

    def _post_system(self, text: str) -> None:
        c = self._chat
        c.config(state=tk.NORMAL)
        c.insert(tk.END, f"\n  ·  {text}  ·\n\n", "system")
        c.config(state=tk.DISABLED)
        c.see(tk.END)

    # ── Game handling ─────────────────────────────────────────────────────────
    def _handle_game(self, args: str) -> None:
        if self._typing_indicator:
            self._typing_indicator.hide()
            self._typing_indicator = None

        if args:
            game = (self._bot.games.get_game_by_index(int(args) - 1)
                    if args.isdigit()
                    else self._bot.games.get_game_by_name(args))
            if game:
                self._open_game_panel(game)
                return

        self._show_game_picker(self._bot.games.get_games())

    def _show_game_picker(self, games: list) -> None:
        pk = tk.Toplevel(self._root)
        pk.title("Choose a Game")
        pk.configure(bg=P.BG_DIALOG)
        pk.resizable(False, False)
        pk.transient(self._root)
        pk.grab_set()

        pw, ph = 400, 460
        pk.update_idletasks()
        px = self._root.winfo_x() + (self._root.winfo_width()  - pw) // 2
        py = self._root.winfo_y() + (self._root.winfo_height() - ph) // 2
        pk.geometry(f"{pw}x{ph}+{px}+{py}")

        tk.Label(pk, text="🎮  Game Zone",
                 bg=P.BG_DIALOG, fg=P.CYAN,
                 font=(P.FONT, 18, "bold")).pack(pady=(30, 4))
        tk.Label(pk, text="Choose your challenge",
                 bg=P.BG_DIALOG, fg=P.TXT_DIM,
                 font=(P.FONT, 10)).pack(pady=(0, 20))

        accents = [P.BLUE, P.VIOLET, P.PINK, P.CYAN]
        for i, game in enumerate(games):
            ac = accents[i % len(accents)]

            def _go(g=game):
                pk.destroy()
                self._open_game_panel(g)

            card = tk.Frame(pk, bg=P.BG_INPUT_PILL, cursor="hand2")
            card.pack(fill=tk.X, padx=28, pady=5)

            tk.Label(card, text=f"{i+1}",
                     bg=P.BG_INPUT_PILL, fg=ac,
                     font=(P.FONT, 14, "bold"),
                     width=3).pack(side=tk.LEFT, pady=14)

            info = tk.Frame(card, bg=P.BG_INPUT_PILL)
            info.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=10)
            tk.Label(info, text=game.name,
                     bg=P.BG_INPUT_PILL, fg=P.TXT_H1,
                     font=(P.FONT, 12, "bold"),
                     anchor=tk.W).pack(fill=tk.X, padx=8)
            tk.Label(info, text=game.description,
                     bg=P.BG_INPUT_PILL, fg=P.TXT_DIM,
                     font=(P.FONT, 9),
                     anchor=tk.W).pack(fill=tk.X, padx=8)

            for w in [card, info] + list(card.winfo_children()) + list(info.winfo_children()):
                try:
                    w.bind("<Button-1>", lambda e, fn=_go: fn())
                    w.bind("<Enter>", lambda e, r=card: r.config(bg=P.BG_HOVER))
                    w.bind("<Leave>", lambda e, r=card: r.config(bg=P.BG_INPUT_PILL))
                except Exception:
                    pass

        tk.Button(pk, text="Cancel",
                  bg=P.BG_DIALOG, fg=P.TXT_DIM,
                  font=(P.FONT, 10), bd=0, cursor="hand2",
                  command=pk.destroy).pack(pady=(16, 28))

    def _open_game_panel(self, game: BaseGame) -> None:
        self._chat_outer.pack_forget()
        self._game_panel.pack(fill=tk.BOTH, expand=True, in_=self._chat_frame)
        self._game_panel_visible = True
        self._root.after(60, lambda: self._game_panel.launch(game))
        self._unlock_input()

    def _close_game_panel(self) -> None:
        self._game_panel.pack_forget()
        self._chat_outer.pack(fill=tk.BOTH, expand=True, in_=self._chat_frame)
        self._game_panel_visible = False
        self._post_system("Game over  ·  welcome back!")
        self._unlock_input()

    # ── GUI-only command handlers ──────────────────────────────────────────────
    def _handle_reset(self) -> None:
        from tkinter import messagebox
        ok = messagebox.askyesno(
            title="Reset Profile",
            message="This will delete your saved name and theme.\n\nAre you sure?",
            icon=messagebox.WARNING,
            parent=self._root,
        )
        if ok:
            self._bot.profile.reset()
            self._bot._user_name = "Friend"
            self._update_user_label("Friend")
            self._post_system("Profile reset  ·  restart Cosmo to set a new name")
        else:
            self._post_bot("❌ Reset cancelled.")
        self._unlock_input()

    def _clear_chat(self) -> None:
        self._chat.config(state=tk.NORMAL)
        self._chat.delete("1.0", tk.END)
        self._chat.config(state=tk.DISABLED)
        self._post_system("Chat cleared")
        self._unlock_input()

    def _update_user_label(self, name: str) -> None:
        try:
            self._user_lbl.config(text=f"  {name}  ")
        except Exception:
            pass

    def _apply_theme(self) -> None:
        """Repaint GUI widgets with the newly selected theme's hex colours."""
        tm  = self._bot.theme
        bg  = tm.hex_color("bg")
        pri = tm.hex_color("primary")
        txt = tm.hex_color("text")
        umg = tm.hex_color("user_msg")
        bmg = tm.hex_color("bot_msg")
        acc = tm.hex_color("accent")

        for w in (self._root, self._col, self._chat_frame,
                  self._chat_outer, self._chat, self._footer,
                  self._input_wrap, self._pill, self._input_text):
            try:
                w.configure(bg=bg)
            except Exception:
                pass

        self._chat.tag_config("user_msg",   background=umg, foreground=txt)
        self._chat.tag_config("bot_msg",    background=bmg, foreground=txt)
        self._chat.tag_config("user_lbl",   foreground=acc)
        self._chat.tag_config("bot_label",  foreground=pri)
        self._chat.tag_config("system",     foreground=acc)
        self._send_btn.configure(bg=acc, activebackground=pri)
        try:
            self._user_lbl.configure(fg=pri, bg=bg)
            self._timer_lbl.configure(fg=txt)
        except Exception:
            pass

    def _cycle_theme(self, _=None) -> None:
        """Sidebar theme button: cycle through all themes in order."""
        names = self._bot.theme.all_names
        cur   = self._bot.theme.current_name
        nxt   = names[(names.index(cur) + 1) % len(names)]
        msg   = self._bot.theme.apply(nxt)
        self._post_system(msg)
        self._root.after(60, self._apply_theme)

    # ── Sidebar action helpers ─────────────────────────────────────────────────
    # (Placeholder wiring — sidebar icons are visual for now,
    #  can be wired to commands in future iterations)

    # ── Animations ────────────────────────────────────────────────────────────
    def _pulse_dot(self, canvas: tk.Canvas) -> None:
        state = {"on": True}

        def _step():
            canvas.itemconfig(1, fill=P.GREEN if state["on"] else P.GREEN_DIM)
            state["on"] = not state["on"]
            canvas.after(1400, _step)

        canvas.after(1400, _step)

    # ── Session timer ─────────────────────────────────────────────────────────
    def _start_timer(self) -> None:
        self._tick_timer()

    def _tick_timer(self) -> None:
        self._session_seconds += 1
        m, s = divmod(self._session_seconds, 60)
        self._timer_lbl.config(text=f"{m:02d}:{s:02d}")
        self._root.after(1000, self._tick_timer)

    # ── Resize ────────────────────────────────────────────────────────────────
    def _on_resize(self, _=None) -> None:
        self._root.after(80, self._apply_margins)

    # ── Onboarding dialog ─────────────────────────────────────────────────────
    def _onboard(self) -> str:
        dlg = tk.Toplevel()
        dlg.title("Welcome to Cosmo AI")
        dlg.configure(bg=P.BG_DIALOG)
        dlg.resizable(False, False)
        dlg.grab_set()

        dw, dh = 460, 320
        dlg.update_idletasks()
        sx = (dlg.winfo_screenwidth()  - dw) // 2
        sy = (dlg.winfo_screenheight() - dh) // 2
        dlg.geometry(f"{dw}x{dh}+{sx}+{sy}")

        tk.Label(dlg, text="✦  Welcome to Cosmo AI",
                 bg=P.BG_DIALOG, fg=P.TXT_H1,
                 font=(P.FONT, 20, "bold")).pack(pady=(36, 4))
        tk.Label(dlg, text="Your cosmic chat companion",
                 bg=P.BG_DIALOG, fg=P.TXT_DIM,
                 font=(P.FONT, 10)).pack()
        tk.Label(dlg, text="What should I call you?",
                 bg=P.BG_DIALOG, fg=P.TXT_LABEL,
                 font=(P.FONT, 12)).pack(pady=(28, 8))

        nv = tk.StringVar()
        ent = tk.Entry(
            dlg, textvariable=nv,
            bg=P.BG_INPUT_PILL, fg=P.TXT_H1,
            insertbackground=P.CYAN,
            font=(P.FONT, 14),
            bd=0, relief=tk.FLAT,
            justify=tk.CENTER,
            highlightthickness=1,
            highlightcolor=P.BLUE,
            highlightbackground=P.BORDER_PILL,
        )
        ent.pack(ipady=12, padx=60, fill=tk.X)
        ent.focus_set()

        res = {"name": ""}

        def _go(_=None):
            res["name"] = nv.get().strip() or "Friend"
            dlg.destroy()

        ent.bind("<Return>", _go)
        tk.Button(
            dlg, text="Start Chatting  →",
            bg=P.BTN_BG, fg="white",
            font=(P.FONT, 12, "bold"),
            bd=0, relief=tk.FLAT, cursor="hand2",
            padx=28, pady=12,
            activebackground=P.BTN_HOVER,
            command=_go,
        ).pack(pady=(20, 0))

        dlg.wait_window()
        return res["name"]

    # ── Run ───────────────────────────────────────────────────────────────────
    def run(self) -> None:
        self._root.mainloop()


# ══════════════════════════════════════════════════════════════════════════════
#  Entry point
# ══════════════════════════════════════════════════════════════════════════════
def main() -> None:
    CosmoGUI().run()


if __name__ == "__main__":
    main()
