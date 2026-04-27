"""
gui.py
──────
Cosmo GUI — Modern Cosmic Edition
A ChatGPT-style Tkinter interface: clean, centered, elegant.

Run with:
    python gui.py

Four classes:
─────────────────────────────────────────────────────────────
  P  (Palette)         — every color, font, spacing constant
  TypingIndicator      — animated "..." dots while Cosmo thinks
  GamePanel            — replaces chat area during a mini-game
  CosmoGUI             — the main window; owns everything
"""

import sys
import threading
import tkinter as tk
from tkinter import font as tkfont

sys.path.insert(0, ".")
from bot   import CosmoBot
from brain import TEACH_PROMPT
from games import BaseGame


# ══════════════════════════════════════════════════════════════
#  P — Palette  (single source of truth for every visual value)
# ══════════════════════════════════════════════════════════════
class P:
    # ── Window ────────────────────────────────────────────────
    WIN_W, WIN_H         = 960, 700
    MIN_W, MIN_H         = 720, 540

    # ── Backgrounds ───────────────────────────────────────────
    BG_WINDOW            = "#0D0F1A"   # outermost — near-black navy
    BG_CHAT              = "#0D0F1A"   # chat column background
    BG_SIDEBAR           = "#0A0C14"   # left sidebar if added later
    BG_INPUT_AREA        = "#0D0F1A"   # footer zone
    BG_INPUT_FIELD       = "#161929"   # the actual text entry
    BG_INPUT_BORDER      = "#262A40"   # border around input field
    BG_USER_MSG          = "#1A2340"   # user bubble
    BG_BOT_MSG           = "#12152A"   # cosmo bubble
    BG_GAME_PANEL        = "#0D0F1A"
    BG_GAME_HEADER       = "#0A0C14"
    BG_DIALOG            = "#0D0F1A"

    # ── Accent colors ─────────────────────────────────────────
    ACCENT_BLUE          = "#4A9EFF"   # primary accent — electric blue (not harsh)
    ACCENT_VIOLET        = "#8B5CF6"   # violet
    ACCENT_CYAN          = "#22D3EE"   # soft cyan
    ACCENT_PINK          = "#EC4899"   # soft pink
    ACCENT_GREEN         = "#10B981"   # success green

    # ── Text ──────────────────────────────────────────────────
    TEXT_PRIMARY         = "#E2E8F0"   # main readable text
    TEXT_SECONDARY       = "#94A3B8"   # metadata, labels
    TEXT_DIM             = "#4A5568"   # timestamps, placeholders
    TEXT_USER            = "#CBD5E1"
    TEXT_BOT             = "#C4C9DE"
    TEXT_ACCENT          = "#4A9EFF"

    # ── Borders & dividers ────────────────────────────────────
    BORDER_SUBTLE        = "#1E2236"
    BORDER_FOCUS         = "#4A9EFF"
    BORDER_BOT_MSG       = "#2D3158"

    # ── Send button ───────────────────────────────────────────
    BTN_SEND             = "#4A9EFF"
    BTN_SEND_HOVER       = "#60B4FF"
    BTN_SEND_DISABLED    = "#2A3550"

    # ── Game panel ────────────────────────────────────────────
    GAME_CORRECT         = "#10B981"
    GAME_WRONG           = "#EC4899"
    GAME_SCORE           = "#8B5CF6"
    GAME_PROMPT          = "#22D3EE"

    # ── Scrollbar ─────────────────────────────────────────────
    SCROLL_BG            = "#0D0F1A"
    SCROLL_FG            = "#1E2A45"

    # ── Fonts ─────────────────────────────────────────────────
    FONT_UI              = "Segoe UI"
    FONT_MONO            = "Courier New"

    # ── Layout ────────────────────────────────────────────────
    CHAT_MAX_WIDTH       = 720        # max width of the centered content column
    BUBBLE_PADDING       = 16
    MSG_SPACING          = 8
    INPUT_RADIUS         = 24         # for the rounded feel
    INPUT_MAX_HEIGHT     = 120        # max height before scrolling
    HEADER_HEIGHT        = 60
    INPUT_AREA_HEIGHT    = 90


# ══════════════════════════════════════════════════════════════
#  TypingIndicator
# ══════════════════════════════════════════════════════════════
class TypingIndicator:
    """
    Inserts an animated  🤖  ●  ●  ● line into the chat Text widget
    while Cosmo is processing.  Replaced by the real response when ready.
    """

    _FRAMES = [
        "  ·  ·  ·",
        "  ●  ·  ·",
        "  ●  ●  ·",
        "  ●  ●  ●",
    ]

    def __init__(self, chat: tk.Text):
        self._chat  = chat
        self._frame = 0
        self._job   = None
        self._start = None   # text index of the indicator line start

    def show(self) -> None:
        self._chat.config(state=tk.NORMAL)
        self._chat.insert(tk.END, "\n", "gap")
        # Insert a placeholder for the Cosmo label
        self._chat.insert(tk.END, "  Cosmo\n", "bot_label")
        self._start = self._chat.index(tk.END + " -1c linestart")
        self._chat.insert(tk.END, "  " + self._FRAMES[0] + "\n", "typing_dot")
        self._chat.config(state=tk.DISABLED)
        self._chat.see(tk.END)
        self._animate()

    def _animate(self) -> None:
        self._frame = (self._frame + 1) % len(self._FRAMES)
        self._chat.config(state=tk.NORMAL)
        try:
            end = self._chat.index(f"{self._start} lineend")
            self._chat.delete(self._start, end)
            self._chat.insert(self._start, "  " + self._FRAMES[self._frame], "typing_dot")
        except tk.TclError:
            pass
        self._chat.config(state=tk.DISABLED)
        self._job = self._chat.after(350, self._animate)

    def hide(self) -> None:
        if self._job:
            self._chat.after_cancel(self._job)
            self._job = None
        self._chat.config(state=tk.NORMAL)
        try:
            if self._start:
                # Remove the label line + the dot line + the gap before them
                block_start = self._chat.index(f"{self._start} -2l linestart")
                block_end   = self._chat.index(f"{self._start} +1l lineend +1c")
                self._chat.delete(block_start, block_end)
        except tk.TclError:
            pass
        self._chat.config(state=tk.DISABLED)
        self._start = None


# ══════════════════════════════════════════════════════════════
#  GamePanel
# ══════════════════════════════════════════════════════════════
class GamePanel(tk.Frame):
    """
    Replaces the chat column while a game is active.
    Uses bot.session.start() and bot.session.answer() exclusively —
    never blocking I/O.
    """

    def __init__(self, parent: tk.Widget, bot: CosmoBot, on_close):
        super().__init__(parent, bg=P.BG_GAME_PANEL)
        self._bot      = bot
        self._on_close = on_close
        self._build()

    # ── Build ─────────────────────────────────────────────────
    def _build(self) -> None:
        """
        Uses grid layout so the order widgets are added never
        affects which ones are visible — fixes the input-bar
        disappearing issue that occurred with pack ordering.

        Grid rows:
          0 — header  (fixed height)
          1 — accent line (1px)
          2 — display area (expands)
          3 — input row (fixed height, always visible)
          4 — return button (hidden until game ends)
        """
        self.grid_rowconfigure(2, weight=1)   # display row expands
        self.grid_columnconfigure(0, weight=1)

        # ── Row 0: Header ──────────────────────────────────────
        hdr = tk.Frame(self, bg=P.BG_GAME_HEADER, height=52)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.pack_propagate(False)

        self._title = tk.Label(
            hdr, text="🎮  Game Zone",
            bg=P.BG_GAME_HEADER, fg=P.ACCENT_CYAN,
            font=(P.FONT_UI, 14, "bold"),
        )
        self._title.pack(side=tk.LEFT, padx=24, pady=12)

        exit_btn = tk.Button(
            hdr, text="← Back to Chat",
            bg=P.BG_GAME_HEADER, fg=P.TEXT_SECONDARY,
            font=(P.FONT_UI, 10), bd=0, cursor="hand2",
            activebackground=P.BG_GAME_HEADER,
            activeforeground=P.TEXT_PRIMARY,
            command=self._close,
        )
        exit_btn.pack(side=tk.RIGHT, padx=20)
        exit_btn.bind("<Enter>", lambda e: exit_btn.config(fg=P.ACCENT_PINK))
        exit_btn.bind("<Leave>", lambda e: exit_btn.config(fg=P.TEXT_SECONDARY))

        # ── Row 1: Accent separator ────────────────────────────
        tk.Frame(self, bg=P.ACCENT_VIOLET, height=1).grid(
            row=1, column=0, sticky="ew")

        # ── Row 2: Display text area ───────────────────────────
        display_wrap = tk.Frame(self, bg=P.BG_GAME_PANEL)
        display_wrap.grid(row=2, column=0, sticky="nsew", padx=60, pady=(16, 8))
        display_wrap.grid_rowconfigure(0, weight=1)
        display_wrap.grid_columnconfigure(0, weight=1)

        scroll = tk.Scrollbar(
            display_wrap, bg=P.SCROLL_BG,
            troughcolor=P.SCROLL_BG,
            activebackground=P.ACCENT_VIOLET,
            width=6,
        )
        scroll.grid(row=0, column=1, sticky="ns")

        self._display = tk.Text(
            display_wrap,
            bg=P.BG_GAME_PANEL, fg=P.TEXT_BOT,
            font=(P.FONT_UI, 12),
            bd=0, relief=tk.FLAT,
            wrap=tk.WORD,
            state=tk.DISABLED,
            padx=4, pady=8,
            cursor="arrow",
            selectbackground=P.BG_USER_MSG,
            spacing1=4, spacing3=4,
            yscrollcommand=scroll.set,
        )
        self._display.grid(row=0, column=0, sticky="nsew")
        scroll.config(command=self._display.yview)
        self._setup_tags()

        # ── Row 3: Input row (always present, never re-packed) ─
        self._input_frame = tk.Frame(self, bg=P.BG_GAME_PANEL)
        self._input_frame.grid(row=3, column=0, sticky="ew", padx=60, pady=(0, 16))
        self._input_frame.grid_columnconfigure(0, weight=1)

        self._answer_var = tk.StringVar()
        self._answer_entry = tk.Entry(
            self._input_frame,
            textvariable=self._answer_var,
            bg=P.BG_INPUT_FIELD, fg=P.TEXT_PRIMARY,
            insertbackground=P.ACCENT_CYAN,
            font=(P.FONT_UI, 13),
            bd=0, relief=tk.FLAT,
            highlightthickness=1,
            highlightcolor=P.ACCENT_VIOLET,
            highlightbackground=P.BG_INPUT_BORDER,
        )
        self._answer_entry.grid(row=0, column=0, sticky="ew", ipady=12, padx=(0, 10))
        self._answer_entry.bind("<Return>", self._submit)

        self._sub_btn = tk.Button(
            self._input_frame,
            text="Submit →",
            bg=P.BTN_SEND, fg="white",
            font=(P.FONT_UI, 11, "bold"),
            bd=0, relief=tk.FLAT, cursor="hand2",
            padx=18, pady=10,
            activebackground=P.BTN_SEND_HOVER,
            command=self._submit,
        )
        self._sub_btn.grid(row=0, column=1)
        self._sub_btn.bind("<Enter>",
            lambda e: self._sub_btn.config(bg=P.BTN_SEND_HOVER))
        self._sub_btn.bind("<Leave>",
            lambda e: self._sub_btn.config(bg=P.BTN_SEND))

        # ── Row 4: Return button (hidden until game ends) ──────
        self._return_btn = tk.Button(
            self, text="← Return to Chat",
            bg=P.ACCENT_VIOLET, fg="white",
            font=(P.FONT_UI, 12, "bold"),
            bd=0, relief=tk.FLAT, cursor="hand2",
            padx=24, pady=11,
            activebackground=P.ACCENT_BLUE,
            command=self._close,
        )
        # Grid row 4 — shown only when game ends via _end_game()

    def _setup_tags(self) -> None:
        # NOTE: tk.Text.tag_config uses 'foreground', not 'fg'
        d = self._display
        d.tag_config("label",
            foreground=P.ACCENT_VIOLET, font=(P.FONT_UI, 10, "bold"))
        d.tag_config("msg",
            foreground=P.TEXT_BOT,     font=(P.FONT_UI, 12))
        d.tag_config("prompt",
            foreground=P.GAME_PROMPT,  font=(P.FONT_UI, 13, "bold"))
        d.tag_config("you",
            foreground=P.ACCENT_BLUE,  font=(P.FONT_UI, 12, "bold"))
        d.tag_config("correct",
            foreground=P.GAME_CORRECT, font=(P.FONT_UI, 12, "bold"))
        d.tag_config("wrong",
            foreground=P.GAME_WRONG,   font=(P.FONT_UI, 12, "bold"))
        d.tag_config("score",
            foreground=P.GAME_SCORE,   font=(P.FONT_UI, 13, "bold"))
        d.tag_config("gap",
            font=(P.FONT_UI, 4))

    # ── Public ────────────────────────────────────────────────
    def launch(self, game: BaseGame) -> None:
        """Start *game* and render the opening prompt."""
        self._bot.session.cancel()
        opening = self._bot.session.start(game)
        self._title.config(text=f"🎮  {game.name}")

        # Hide return button (grid_remove keeps its grid config intact)
        self._return_btn.grid_remove()
        # Ensure input row is visible
        self._input_frame.grid(row=3, column=0, sticky="ew",
                               padx=60, pady=(0, 16))
        self._answer_entry.config(state=tk.NORMAL)
        self._sub_btn.config(state=tk.NORMAL)
        self._answer_var.set("")

        # Render opening content
        self._clear()
        self._write("label",  "  Cosmo\n")
        self._write("msg",    "  " + opening["message"] + "\n\n")
        # Render each line of the prompt separately
        for pline in opening.get("prompt", "").split("\n"):
            if pline.strip():
                self._write("prompt", "  " + pline + "\n")

        # Defer focus so widget is fully mapped
        self.after(80, self._answer_entry.focus_set)

    # ── Private ────────────────────────────────────────────────
    def _submit(self, _=None) -> None:
        text = self._answer_var.get().strip()
        if not text:
            return
        self._answer_var.set("")
        self._write("gap", "\n")
        self._write("you", f"  You:  {text}\n")

        result = self._bot.session.answer(text)
        msg    = result["message"]

        self._write("gap", "\n")
        for line in msg.split("\n"):
            if not line.strip():
                self._write("gap", "\n")
                continue
            if any(k in line for k in ("Final Score", "🎯", "🏆", "🌟", "👍", "📚")):
                self._write("score", "  " + line + "\n")
            elif "\u2705" in line:
                self._write("correct", "  " + line + "\n")
            elif "\u274c" in line or "\u26a0\ufe0f" in line:
                self._write("wrong", "  " + line + "\n")
            else:
                self._write("msg", "  " + line + "\n")

        if result.get("done"):
            self._end_game()
        else:
            # Render the prompt (options / answer field label) as its own block
            if result.get("prompt"):
                self._write("gap", "\n")
                # Each line of the prompt on its own line for readability
                for pline in result["prompt"].split("\n"):
                    if pline.strip():
                        self._write("prompt", "  " + pline + "\n")
            # Keep focus on entry for next answer
            self.after(10, self._answer_entry.focus_set)

    def _end_game(self) -> None:
        """Disable input, hide input row, show Return button."""
        self._answer_entry.config(state=tk.DISABLED)
        self._sub_btn.config(state=tk.DISABLED)
        # Remove input row from grid; show return button in row 4
        self._input_frame.grid_remove()
        self._return_btn.grid(row=4, column=0, pady=(4, 24))
        self.after(50, self._return_btn.focus_set)

    def _close(self) -> None:
        self._bot.session.cancel()
        self._on_close()

    def _clear(self) -> None:
        self._display.config(state=tk.NORMAL)
        self._display.delete("1.0", tk.END)
        self._display.config(state=tk.DISABLED)

    def _write(self, tag: str, text: str) -> None:
        self._display.config(state=tk.NORMAL)
        self._display.insert(tk.END, text, tag)
        self._display.config(state=tk.DISABLED)
        self._display.see(tk.END)


# ══════════════════════════════════════════════════════════════
#  CosmoGUI — main window
# ══════════════════════════════════════════════════════════════
class CosmoGUI:
    """
    Main application window.

    Layout:
      ┌──────────────────────────────────────┐
      │  Header (title + status)             │
      ├──────────────────────────────────────┤
      │  Chat area  ← centered column        │
      │  (scrollable, max-width constrained) │
      ├──────────────────────────────────────┤
      │  Input container (floating style)    │
      │  [  Message Cosmo...          ] [→]  │
      └──────────────────────────────────────┘
    """

    def __init__(self):
        # ── Backend ───────────────────────────────────────────
        self._bot = CosmoBot()
        self._bot.boot()

        # ── Root window ───────────────────────────────────────
        self._root = tk.Tk()
        self._root.title("Cosmo AI")
        self._root.configure(bg=P.BG_WINDOW)
        self._root.minsize(P.MIN_W, P.MIN_H)

        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        x  = (sw - P.WIN_W) // 2
        y  = (sh - P.WIN_H) // 2
        self._root.geometry(f"{P.WIN_W}x{P.WIN_H}+{x}+{y}")

        # ── State ─────────────────────────────────────────────
        self._teach_pending      = False
        self._session_seconds    = 0
        self._typing_indicator   = None
        self._input_height       = 44   # dynamic input box height
        self._game_panel_visible = False

        # ── Onboarding ────────────────────────────────────────
        if self._bot.profile.is_new_user():
            name = self._onboard()
            self._bot.initialize_user(name or "Friend")
        self._bot.profile.load()
        self._bot.theme.load()

        # ── Build UI ──────────────────────────────────────────
        self._build_header()
        self._build_main_area()
        self._build_input_area()

        # ── Keyboard bindings ─────────────────────────────────
        self._root.bind("<Configure>", self._on_window_resize)

        # ── Welcome ───────────────────────────────────────────
        name = self._bot.profile.name
        self._post_bot_message(
            f"Hey {name}! 👋  I'm Cosmo — your cosmic AI companion.\n"
            f"Chat with me naturally, or try  !help  to see what I can do."
        )
        self._start_timer()
        self._input_text.focus_set()

    # ══════════════════════════════════════════════════════════
    #  Header
    # ══════════════════════════════════════════════════════════
    def _build_header(self) -> None:
        self._header = tk.Frame(
            self._root, bg=P.BG_WINDOW, height=P.HEADER_HEIGHT,
        )
        self._header.pack(fill=tk.X, side=tk.TOP)
        self._header.pack_propagate(False)

        # Left: avatar dot + title
        left = tk.Frame(self._header, bg=P.BG_WINDOW)
        left.pack(side=tk.LEFT, padx=28, pady=0)
        left.pack_configure(anchor=tk.W)

        # Pulsing status dot (canvas circle)
        dot_c = tk.Canvas(left, width=10, height=10,
                          bg=P.BG_WINDOW, highlightthickness=0)
        dot_c.pack(side=tk.LEFT, padx=(0, 10), pady=22)
        dot_c.create_oval(1, 1, 9, 9, fill=P.ACCENT_GREEN, outline="")
        self._pulse_dot(dot_c)

        title_col = tk.Frame(left, bg=P.BG_WINDOW)
        title_col.pack(side=tk.LEFT)

        tk.Label(
            title_col, text="Cosmo AI",
            bg=P.BG_WINDOW, fg=P.TEXT_PRIMARY,
            font=(P.FONT_UI, 15, "bold"),
        ).pack(anchor=tk.W)
        tk.Label(
            title_col, text="Your cosmic chat companion",
            bg=P.BG_WINDOW, fg=P.TEXT_DIM,
            font=(P.FONT_UI, 9),
        ).pack(anchor=tk.W)

        # Right: user name + timer
        right = tk.Frame(self._header, bg=P.BG_WINDOW)
        right.pack(side=tk.RIGHT, padx=28)

        self._user_lbl = tk.Label(
            right,
            text=f"👤  {self._bot.profile.name}",
            bg=P.BG_WINDOW, fg=P.TEXT_SECONDARY,
            font=(P.FONT_UI, 10),
        )
        self._user_lbl.pack(anchor=tk.E)

        self._timer_lbl = tk.Label(
            right, text="00:00",
            bg=P.BG_WINDOW, fg=P.TEXT_DIM,
            font=(P.FONT_UI, 9),
        )
        self._timer_lbl.pack(anchor=tk.E)

        # Bottom border
        tk.Frame(self._root, bg=P.BORDER_SUBTLE, height=1).pack(fill=tk.X)

    # ══════════════════════════════════════════════════════════
    #  Main area (chat column + game panel, stacked)
    # ══════════════════════════════════════════════════════════
    def _build_main_area(self) -> None:
        self._main = tk.Frame(self._root, bg=P.BG_CHAT)
        self._main.pack(fill=tk.BOTH, expand=True)

        # ── Chat scroll area ──────────────────────────────────
        self._chat_outer = tk.Frame(self._main, bg=P.BG_CHAT)
        self._chat_outer.pack(fill=tk.BOTH, expand=True)

        # Thin scrollbar on the right edge
        self._scrollbar = tk.Scrollbar(
            self._chat_outer,
            bg=P.SCROLL_BG, troughcolor=P.SCROLL_BG,
            activebackground=P.ACCENT_VIOLET,
            width=6,
        )
        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._chat = tk.Text(
            self._chat_outer,
            bg=P.BG_CHAT, fg=P.TEXT_PRIMARY,
            font=(P.FONT_UI, 12),
            bd=0, relief=tk.FLAT,
            wrap=tk.WORD,
            state=tk.DISABLED,
            cursor="arrow",
            selectbackground=P.BG_USER_MSG,
            yscrollcommand=self._scrollbar.set,
            spacing1=0, spacing3=0,
            padx=0, pady=0,
        )
        self._chat.pack(fill=tk.BOTH, expand=True)
        self._scrollbar.config(command=self._chat.yview)
        self._setup_chat_tags()

        # ── Game panel (hidden initially) ─────────────────────
        self._game_panel = GamePanel(
            self._main, self._bot,
            on_close=self._close_game_panel,
        )

    def _setup_chat_tags(self) -> None:
        c = self._chat

        # Outer padding rows — give the column breathing room
        c.tag_config("gap",        font=(P.FONT_UI, 5))
        c.tag_config("big_gap",    font=(P.FONT_UI, 10))

        # Centering: left margin = dynamic (set on resize), right margin mirrors
        c.tag_config("user_label",
            foreground=P.TEXT_DIM,
            font=(P.FONT_UI, 9),
            justify=tk.RIGHT,
        )
        c.tag_config("user_msg",
            background=P.BG_USER_MSG,
            foreground=P.TEXT_USER,
            font=(P.FONT_UI, 12),
            justify=tk.RIGHT,
            spacing1=P.BUBBLE_PADDING,
            spacing3=P.BUBBLE_PADDING,
        )
        c.tag_config("bot_label",
            foreground=P.ACCENT_VIOLET,
            font=(P.FONT_UI, 9, "bold"),
        )
        c.tag_config("bot_msg",
            background=P.BG_BOT_MSG,
            foreground=P.TEXT_BOT,
            font=(P.FONT_UI, 12),
            spacing1=P.BUBBLE_PADDING,
            spacing3=P.BUBBLE_PADDING,
        )
        c.tag_config("system",
            foreground=P.TEXT_DIM,
            font=(P.FONT_UI, 10, "italic"),
            justify=tk.CENTER,
        )
        c.tag_config("typing_dot",
            foreground=P.ACCENT_VIOLET,
            font=(P.FONT_UI, 12),
        )

        # Apply margin immediately
        self._root.after(50, self._apply_chat_margins)

    def _apply_chat_margins(self) -> None:
        """
        Calculate side margins so the chat content stays
        centered in a max-width column — just like ChatGPT.
        """
        w = self._chat.winfo_width()
        if w < 100:
            self._root.after(100, self._apply_chat_margins)
            return

        col_w    = min(P.CHAT_MAX_WIDTH, w - 60)
        side_pad = max(24, (w - col_w) // 2)

        for tag in ("user_msg", "user_label"):
            self._chat.tag_config(
                tag,
                lmargin1=side_pad + 80,
                lmargin2=side_pad + 80,
                rmargin=side_pad,
            )
        for tag in ("bot_msg", "bot_label"):
            self._chat.tag_config(
                tag,
                lmargin1=side_pad,
                lmargin2=side_pad,
                rmargin=side_pad + 80,
            )
        self._chat.tag_config(
            "system",
            lmargin1=side_pad,
            lmargin2=side_pad,
            rmargin=side_pad,
        )

    # ══════════════════════════════════════════════════════════
    #  Input area — floating container above bottom edge
    # ══════════════════════════════════════════════════════════
    def _build_input_area(self) -> None:

        # Thin separator
        tk.Frame(self._root, bg=P.BORDER_SUBTLE, height=1).pack(fill=tk.X)

        # Footer background zone
        self._footer = tk.Frame(self._root, bg=P.BG_INPUT_AREA)
        self._footer.pack(fill=tk.X, side=tk.BOTTOM)

        # Centered container — gives the floating / elevated look
        self._input_container = tk.Frame(
            self._footer, bg=P.BG_INPUT_AREA,
        )
        self._input_container.pack(
            fill=tk.X, padx=0, pady=16,
        )

        # The "pill" input box frame — rounded feel via padding
        self._input_pill = tk.Frame(
            self._input_container,
            bg=P.BG_INPUT_FIELD,
            highlightthickness=1,
            highlightbackground=P.BG_INPUT_BORDER,
            highlightcolor=P.BORDER_FOCUS,
        )
        self._input_pill.pack(
            fill=tk.X, padx=120, ipady=0,
        )

        # The multiline Text widget (replaces Entry for Shift+Enter support)
        self._input_text = tk.Text(
            self._input_pill,
            bg=P.BG_INPUT_FIELD, fg=P.TEXT_PRIMARY,
            insertbackground=P.ACCENT_CYAN,
            font=(P.FONT_UI, 13),
            bd=0, relief=tk.FLAT,
            wrap=tk.WORD,
            height=1,
            padx=16, pady=12,
        )
        self._input_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._input_text.bind("<Return>",       self._on_enter)
        self._input_text.bind("<Shift-Return>", self._on_shift_enter)
        self._input_text.bind("<KeyRelease>",   self._on_key_release)
        self._input_text.bind("<FocusIn>",      self._on_focus_in)
        self._input_text.bind("<FocusOut>",     self._on_focus_out)

        # Placeholder text
        self._placeholder_active = True
        self._show_placeholder()

        # Send button (paper-plane / arrow icon)
        self._send_btn = tk.Button(
            self._input_pill,
            text="↑",
            font=(P.FONT_UI, 16, "bold"),
            bg=P.BTN_SEND, fg="white",
            activebackground=P.BTN_SEND_HOVER,
            bd=0, relief=tk.FLAT,
            cursor="hand2",
            padx=14, pady=8,
            command=self._on_send,
        )
        self._send_btn.pack(side=tk.RIGHT, padx=(4, 6), pady=6)
        self._send_btn.bind(
            "<Enter>", lambda e: self._send_btn.config(bg=P.BTN_SEND_HOVER))
        self._send_btn.bind(
            "<Leave>", lambda e: self._send_btn.config(bg=P.BTN_SEND))

        # Hint row
        tk.Label(
            self._input_container,
            text="Enter to send  ·  Shift+Enter for new line",
            bg=P.BG_INPUT_AREA, fg=P.TEXT_DIM,
            font=(P.FONT_UI, 8),
        ).pack(pady=(6, 0))

    # ══════════════════════════════════════════════════════════
    #  Placeholder helpers
    # ══════════════════════════════════════════════════════════
    def _show_placeholder(self) -> None:
        self._input_text.insert("1.0", "Message Cosmo...")
        self._input_text.config(fg=P.TEXT_DIM)
        self._placeholder_active = True

    def _hide_placeholder(self) -> None:
        if self._placeholder_active:
            self._input_text.delete("1.0", tk.END)
            self._input_text.config(fg=P.TEXT_PRIMARY)
            self._placeholder_active = False

    def _on_focus_in(self, _=None) -> None:
        self._hide_placeholder()
        self._input_pill.config(highlightbackground=P.BORDER_FOCUS)

    def _on_focus_out(self, _=None) -> None:
        self._input_pill.config(highlightbackground=P.BG_INPUT_BORDER)
        if not self._input_text.get("1.0", tk.END).strip():
            self._show_placeholder()

    # ══════════════════════════════════════════════════════════
    #  Input events
    # ══════════════════════════════════════════════════════════
    def _on_enter(self, event) -> str:
        """Enter key → send message."""
        self._on_send()
        return "break"   # prevent default newline insertion

    def _on_shift_enter(self, event) -> None:
        """Shift+Enter → insert a real newline, resize input."""
        # Let the default binding insert the newline, then resize
        self._root.after(10, self._resize_input)

    def _on_key_release(self, _=None) -> None:
        """Resize the input box as content grows."""
        if not self._placeholder_active:
            self._resize_input()

    def _resize_input(self) -> None:
        """Dynamically grow/shrink the Text widget height (1–5 lines)."""
        lines = int(self._input_text.index(tk.END).split(".")[0]) - 1
        lines = max(1, min(lines, 5))
        self._input_text.config(height=lines)

    # ══════════════════════════════════════════════════════════
    #  Sending & delivering messages
    # ══════════════════════════════════════════════════════════
    def _on_send(self, _=None) -> None:
        if self._placeholder_active:
            return
        text = self._input_text.get("1.0", tk.END).strip()
        if not text:
            return

        # Clear input
        self._input_text.delete("1.0", tk.END)
        self._input_text.config(height=1)
        self._show_placeholder()
        self._lock_input()

        # Render user bubble
        self._post_user_message(text)

        # Teach mode?
        if self._teach_pending:
            self._teach_pending = False
            if text.lower() in ("no", "n", "nope", "skip"):
                reply = self._bot.teach_confirm(False)
            else:
                reply = self._bot.teach_confirm(True, text)
            self._post_bot_message(reply)
            self._unlock_input()
            return

        # Commands handled entirely in the GUI (no typing delay needed)
        lower_t = text.strip().lower()
        if lower_t in ("!reset", "/reset"):
            self._handle_reset()
            return
        if lower_t in ("!clear", "/clear"):
            self._clear_chat()
            return

        # Game command? (explicit !game prefix or natural language trigger)
        if lower_t.startswith("!game") or lower_t.startswith("/game"):
            args = text.split(None, 1)[1].strip() if len(text.split()) > 1 else ""
            self._show_typing_then(lambda: self._handle_game(args))
            return

        # Normal message — show typing indicator then deliver
        self._show_typing_then(lambda: self._deliver(text))

    def _show_typing_then(self, callback) -> None:
        """Show the typing indicator, wait 900ms, call callback."""
        self._typing_indicator = TypingIndicator(self._chat)
        self._typing_indicator.show()
        self._root.after(900, callback)

    def _deliver(self, text: str) -> None:
        """Hide typing indicator and post Cosmo's response."""
        if self._typing_indicator:
            self._typing_indicator.hide()
            self._typing_indicator = None

        # ── GUI-specific intercepts ────────────────────────────
        # !reset  → show a custom confirm dialog instead of input()
        lower = text.strip().lower()
        if lower in ("!reset", "/reset"):
            self._handle_reset()
            return

        # !clear  → clear the visible chat widget
        if lower in ("!clear", "/clear"):
            self._clear_chat()
            return

        # ── Normal backend processing ──────────────────────────
        response, session_ended = self._bot.process_message(text)

        if session_ended:
            self._post_bot_message(response)
            self._post_system("Session ended. Restart Cosmo to continue.")
            return   # leave input locked

        if response == TEACH_PROMPT:
            self._teach_pending = True
            self._post_bot_message(
                "Hmm, I don't know that one. 🤔\n"
                "Want to teach me? Type your reply — or 'no' to skip."
            )
            self._unlock_input()
            return

        # Empty response = engine printed game menu to stdout (CLI path).
        # In the GUI we show the game picker instead.
        if response == "":
            self._handle_game("")
            return

        if response:
            self._post_bot_message(response)
            # If the theme changed, repaint the GUI immediately
            if "Theme changed" in response or "✨" in response:
                self._root.after(50, self._apply_theme)

        self._unlock_input()

    def _lock_input(self) -> None:
        self._input_text.config(state=tk.DISABLED)
        self._send_btn.config(state=tk.DISABLED, bg=P.BTN_SEND_DISABLED)

    def _unlock_input(self) -> None:
        self._input_text.config(state=tk.NORMAL)
        self._send_btn.config(state=tk.NORMAL, bg=P.BTN_SEND)
        self._hide_placeholder()
        self._input_text.focus_set()

    # ══════════════════════════════════════════════════════════
    #  Message rendering
    # ══════════════════════════════════════════════════════════
    def _post_user_message(self, text: str) -> None:
        c = self._chat
        c.config(state=tk.NORMAL)
        c.insert(tk.END, "\n", "big_gap")
        c.insert(tk.END, f"  You  \n", "user_label")
        # Pad text for the bubble feel
        padded = "\n".join(f"  {line}  " for line in text.split("\n"))
        c.insert(tk.END, padded + "\n", "user_msg")
        c.config(state=tk.DISABLED)
        c.see(tk.END)

    def _post_bot_message(self, text: str) -> None:
        c = self._chat
        c.config(state=tk.NORMAL)
        c.insert(tk.END, "\n", "big_gap")
        c.insert(tk.END, "  Cosmo\n", "bot_label")
        padded = "\n".join(f"  {line}  " for line in text.split("\n"))
        c.insert(tk.END, padded + "\n", "bot_msg")
        c.config(state=tk.DISABLED)
        c.see(tk.END)

    def _post_system(self, text: str) -> None:
        c = self._chat
        c.config(state=tk.NORMAL)
        c.insert(tk.END, f"\n  —  {text}  —\n\n", "system")
        c.config(state=tk.DISABLED)
        c.see(tk.END)

    # ══════════════════════════════════════════════════════════
    #  Game handling
    # ══════════════════════════════════════════════════════════
    def _handle_game(self, args: str) -> None:
        if self._typing_indicator:
            self._typing_indicator.hide()
            self._typing_indicator = None

        games = self._bot.games.get_games()

        if args:
            game = (self._bot.games.get_game_by_index(int(args) - 1)
                    if args.isdigit()
                    else self._bot.games.get_game_by_name(args))
            if game:
                self._open_game_panel(game)
                return

        self._show_game_picker(games)

    def _show_game_picker(self, games: list) -> None:
        pick = tk.Toplevel(self._root)
        pick.title("Choose a Game")
        pick.configure(bg=P.BG_DIALOG)
        pick.resizable(False, False)
        pick.transient(self._root)
        pick.grab_set()

        pw, ph = 380, 440
        pick.update_idletasks()
        px = self._root.winfo_x() + (self._root.winfo_width()  - pw) // 2
        py = self._root.winfo_y() + (self._root.winfo_height() - ph) // 2
        pick.geometry(f"{pw}x{ph}+{px}+{py}")

        tk.Label(pick, text="🎮  Game Zone",
                 bg=P.BG_DIALOG, fg=P.ACCENT_CYAN,
                 font=(P.FONT_UI, 17, "bold")).pack(pady=(28, 4))
        tk.Label(pick, text="Choose your challenge",
                 bg=P.BG_DIALOG, fg=P.TEXT_DIM,
                 font=(P.FONT_UI, 10)).pack(pady=(0, 20))

        accent_cycle = [P.ACCENT_BLUE, P.ACCENT_VIOLET, P.ACCENT_PINK, P.ACCENT_CYAN]
        for i, game in enumerate(games):
            accent = accent_cycle[i % len(accent_cycle)]

            def _launch(g=game):
                pick.destroy()
                self._open_game_panel(g)

            row = tk.Frame(pick, bg=P.BG_INPUT_FIELD, cursor="hand2")
            row.pack(fill=tk.X, padx=24, pady=5)

            tk.Label(row, text=f"  {i+1}",
                     bg=P.BG_INPUT_FIELD, fg=accent,
                     font=(P.FONT_UI, 13, "bold"),
                     width=3).pack(side=tk.LEFT, pady=14)

            info = tk.Frame(row, bg=P.BG_INPUT_FIELD)
            info.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=10)
            tk.Label(info, text=game.name,
                     bg=P.BG_INPUT_FIELD, fg=P.TEXT_PRIMARY,
                     font=(P.FONT_UI, 12, "bold"),
                     anchor=tk.W).pack(fill=tk.X, padx=8)
            tk.Label(info, text=game.description,
                     bg=P.BG_INPUT_FIELD, fg=P.TEXT_DIM,
                     font=(P.FONT_UI, 9),
                     anchor=tk.W).pack(fill=tk.X, padx=8)

            row.bind("<Button-1>", lambda e, fn=_launch: fn())
            for child in row.winfo_children():
                child.bind("<Button-1>", lambda e, fn=_launch: fn())
            for child in info.winfo_children():
                child.bind("<Button-1>", lambda e, fn=_launch: fn())

            row.bind("<Enter>", lambda e, r=row: r.config(bg=P.BG_USER_MSG))
            row.bind("<Leave>", lambda e, r=row: r.config(bg=P.BG_INPUT_FIELD))

        tk.Button(pick, text="Cancel",
                  bg=P.BG_DIALOG, fg=P.TEXT_DIM,
                  font=(P.FONT_UI, 10), bd=0, cursor="hand2",
                  command=pick.destroy).pack(pady=(16, 24))

    def _open_game_panel(self, game: BaseGame) -> None:
        # Hide the chat area
        self._chat_outer.pack_forget()
        # Show the game panel in its place (inside self._main)
        self._game_panel.pack(fill=tk.BOTH, expand=True, in_=self._main)
        self._game_panel_visible = True
        # Let Tkinter finish drawing the panel, then launch the game
        self._root.after(60, lambda: self._game_panel.launch(game))

    def _close_game_panel(self) -> None:
        # Hide game panel, restore chat area inside _main
        self._game_panel.pack_forget()
        self._chat_outer.pack(fill=tk.BOTH, expand=True, in_=self._main)
        self._game_panel_visible = False
        self._post_system("Game over — welcome back!")
        self._unlock_input()

    # ══════════════════════════════════════════════════════════
    #  GUI-only command handlers
    # ══════════════════════════════════════════════════════════
    def _handle_reset(self) -> None:
        """
        Show a native confirm dialog, then reset the profile if confirmed.
        Replaces the CLI input()-based confirmation.
        """
        from tkinter import messagebox
        confirmed = messagebox.askyesno(
            title  = "Reset Profile",
            message= (
                "This will delete your saved name and theme preference.\n\n"
                "Are you sure you want to reset your profile?"
            ),
            icon   = messagebox.WARNING,
            parent = self._root,
        )
        if confirmed:
            self._bot.profile.reset()
            self._bot._user_name = "Friend"
            self._post_system("Profile reset. Restart Cosmo to set a new name.")
            self._update_user_label("Friend")
        else:
            self._post_bot_message("❌ Reset cancelled.")
        self._unlock_input()

    def _clear_chat(self) -> None:
        """Clear all messages from the visible chat widget."""
        self._chat.config(state=tk.NORMAL)
        self._chat.delete("1.0", tk.END)
        self._chat.config(state=tk.DISABLED)
        self._post_system("Chat cleared.")
        self._unlock_input()

    def _update_user_label(self, name: str) -> None:
        """Update the header user label after a name change or reset."""
        try:
            self._user_lbl.config(text=f"👤  {name}")
        except Exception:
            pass

    def _apply_theme(self) -> None:
        """
        Re-apply the active theme's hex colours to the GUI widgets.
        Called after !theme switches the theme so the interface
        actually repaints — not just the CLI text colour.
        """
        tm = self._bot.theme

        # Window and major backgrounds
        bg = tm.hex_color("bg")
        self._root.configure(bg=bg)
        self._header.configure(bg=bg)
        self._main.configure(bg=bg)
        self._chat_outer.configure(bg=bg)
        self._chat.configure(bg=bg)
        self._footer.configure(bg=bg)
        self._input_container.configure(bg=bg)
        self._input_pill.configure(bg=bg)
        self._input_text.configure(bg=bg)

        # Chat bubble tag colours
        user_bg  = tm.hex_color("user_msg")
        bot_bg   = tm.hex_color("bot_msg")
        primary  = tm.hex_color("primary")
        text_col = tm.hex_color("text")

        self._chat.tag_config("user_msg",   background=user_bg,  foreground=text_col)
        self._chat.tag_config("bot_msg",    background=bot_bg,   foreground=text_col)
        self._chat.tag_config("user_label", foreground=primary)
        self._chat.tag_config("bot_label",  foreground=primary)
        self._chat.tag_config("system",     foreground=primary)

        # Send button accent
        accent = tm.hex_color("accent")
        self._send_btn.configure(bg=accent, activebackground=primary)

        # Header user label accent
        try:
            self._user_lbl.configure(fg=text_col)
            self._timer_lbl.configure(fg=text_col)
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════
    #  Animations
    # ══════════════════════════════════════════════════════════
    def _pulse_dot(self, canvas: tk.Canvas) -> None:
        """Alternate the status dot between bright and dim green."""
        state = {"bright": True}

        def _step():
            color = P.ACCENT_GREEN if state["bright"] else "#0D4A2A"
            canvas.itemconfig(1, fill=color)
            state["bright"] = not state["bright"]
            canvas.after(1200, _step)

        canvas.after(1200, _step)

    # ══════════════════════════════════════════════════════════
    #  Session timer
    # ══════════════════════════════════════════════════════════
    def _start_timer(self) -> None:
        self._tick_timer()

    def _tick_timer(self) -> None:
        self._session_seconds += 1
        m = self._session_seconds // 60
        s = self._session_seconds % 60
        self._timer_lbl.config(text=f"{m:02d}:{s:02d}")
        self._root.after(1000, self._tick_timer)

    # ══════════════════════════════════════════════════════════
    #  Resize handler
    # ══════════════════════════════════════════════════════════
    def _on_window_resize(self, _=None) -> None:
        self._root.after(80, self._apply_chat_margins)

    # ══════════════════════════════════════════════════════════
    #  Onboarding dialog
    # ══════════════════════════════════════════════════════════
    def _onboard(self) -> str:
        dlg = tk.Toplevel()
        dlg.title("Welcome to Cosmo")
        dlg.configure(bg=P.BG_DIALOG)
        dlg.resizable(False, False)
        dlg.grab_set()

        dw, dh = 440, 300
        dlg.update_idletasks()
        sx = (dlg.winfo_screenwidth()  - dw) // 2
        sy = (dlg.winfo_screenheight() - dh) // 2
        dlg.geometry(f"{dw}x{dh}+{sx}+{sy}")

        tk.Label(dlg, text="Welcome to Cosmo AI",
                 bg=P.BG_DIALOG, fg=P.TEXT_PRIMARY,
                 font=(P.FONT_UI, 18, "bold")).pack(pady=(36, 4))
        tk.Label(dlg, text="Your cosmic chat companion",
                 bg=P.BG_DIALOG, fg=P.TEXT_DIM,
                 font=(P.FONT_UI, 10)).pack()
        tk.Label(dlg, text="What should I call you?",
                 bg=P.BG_DIALOG, fg=P.TEXT_SECONDARY,
                 font=(P.FONT_UI, 12)).pack(pady=(24, 8))

        name_var = tk.StringVar()
        entry = tk.Entry(
            dlg,
            textvariable=name_var,
            bg=P.BG_INPUT_FIELD, fg=P.TEXT_PRIMARY,
            insertbackground=P.ACCENT_CYAN,
            font=(P.FONT_UI, 14),
            bd=0, relief=tk.FLAT,
            justify=tk.CENTER,
            highlightthickness=1,
            highlightcolor=P.ACCENT_BLUE,
            highlightbackground=P.BG_INPUT_BORDER,
        )
        entry.pack(ipady=11, padx=50, fill=tk.X)
        entry.focus_set()

        result = {"name": ""}

        def _go(_=None):
            result["name"] = name_var.get().strip() or "Friend"
            dlg.destroy()

        entry.bind("<Return>", _go)
        tk.Button(
            dlg, text="Start Chatting →",
            bg=P.BTN_SEND, fg="white",
            font=(P.FONT_UI, 12, "bold"),
            bd=0, relief=tk.FLAT,
            cursor="hand2",
            padx=24, pady=10,
            activebackground=P.BTN_SEND_HOVER,
            command=_go,
        ).pack(pady=(16, 0))

        dlg.wait_window()
        return result["name"]

    # ══════════════════════════════════════════════════════════
    #  Run
    # ══════════════════════════════════════════════════════════
    def run(self) -> None:
        self._root.mainloop()


# ══════════════════════════════════════════════════════════════
#  Entry point
# ══════════════════════════════════════════════════════════════
def main() -> None:
    app = CosmoGUI()
    app.run()


if __name__ == "__main__":
    main()
