"""
brain.py
────────
Everything that makes Cosmo think and respond — three classes
that share one job: turning raw user input into a useful reply.

  Calculator       — maths
                     Safely evaluates expressions like "sqrt(16)"
                     in a sandboxed namespace. Never raises —
                     all errors returned as friendly strings.

  ResponseEngine   — conversation
                     Loads responses.json, maps user text to one
                     of 23 intent categories via keyword lookup,
                     handles dynamic placeholders ({time} etc.),
                     delegates maths to Calculator, and manages
                     the two-phase "teach Cosmo" flow.

  CommandHandler   — commands
                     Parses !-prefixed commands, routes each one
                     to the right sub-system, and always returns
                     a plain string the CLI or GUI can display.

Teaching flow (ResponseEngine)
──────────────────────────────
  When get_response() cannot match input for the 2nd time in a
  row it returns the module constant TEACH_PROMPT instead of
  blocking on input(). The caller detects this signal and later
  calls confirm_teach() with the user's answer. This keeps all
  I/O completely out of the engine.

TEACH_PROMPT = "__TEACH_PROMPT__"
"""

from __future__ import annotations

import datetime
import json
import math
import os
import random
from typing import TYPE_CHECKING

from colorama import Fore, Style

if TYPE_CHECKING:
    from games import GameManager
    from memory import Logger, UserProfile
    from theme import ThemeManager

# ── Public signal constant ─────────────────────────────────────
TEACH_PROMPT: str = "__TEACH_PROMPT__"


# ══════════════════════════════════════════════════════════════
#  Calculator
# ══════════════════════════════════════════════════════════════
class Calculator:
    """Evaluates math expressions in a whitelisted sandbox."""

    _SAFE_NAMESPACE: dict = {
        "sqrt":  math.sqrt,  "sin":   math.sin,   "cos":  math.cos,
        "tan":   math.tan,   "log":   math.log,    "log10": math.log10,
        "exp":   math.exp,   "pi":    math.pi,     "e":    math.e,
        "abs":   abs,        "round": round,        "pow":  pow,
        "ceil":  math.ceil,  "floor": math.floor,
    }

    def evaluate(self, expression: str) -> str:
        """
        Evaluate *expression* and return a formatted result string.
        Never raises — all errors become descriptive error strings.
        """
        if not expression.strip():
            return "❓ Please provide an expression. Example: !calc 2 + 2"
        try:
            result = eval(expression, {"__builtins__": {}}, self._SAFE_NAMESPACE)
            # Clean floating-point noise: 4.0 → 4
            if isinstance(result, float) and result == int(result):
                result = int(result)
            return f"🧮 {expression} = {result}"
        except ZeroDivisionError:
            return "⚠️  Error: Cannot divide by zero!"
        except SyntaxError:
            return "⚠️  Error: Invalid mathematical expression."
        except NameError:
            return (
                "⚠️  Error: Unknown function or variable. "
                "Supported: +, -, *, /, **, sqrt(), sin(), cos(), "
                "tan(), log(), exp(), pi, e, ceil(), floor()"
            )
        except Exception as exc:
            return f"⚠️  Error calculating: {exc}"


# ══════════════════════════════════════════════════════════════
#  ResponseEngine
# ══════════════════════════════════════════════════════════════
class ResponseEngine:
    """
    Loads responses.json, matches user intent via keywords,
    and returns response strings. Completely I/O-free — safe
    to use from both the CLI and Tkinter GUI.
    """

    # 23 intent categories, each with a list of trigger keywords
    TRIGGERS: dict[str, list[str]] = {
        "greeting":    ["hi", "hello", "hey", "sup", "hiya", "howdy", "greetings",
                        "good morning", "good afternoon", "good evening"],
        "farewell":    ["bye", "goodbye", "see you", "later", "farewell", "cya",
                        "see ya", "take care"],
        "time":        ["time", "clock", "what time", "current time"],
        "date":        ["date", "day", "today", "what day", "current date"],
        "joke":        ["joke", "funny", "laugh", "make me laugh", "tell me a joke",
                        "humor", "humour", "something funny"],
        "feeling":     ["how are you", "feeling", "mood", "you okay", "you good",
                        "how do you feel", "how r u"],
        "acknowledge": ["ok", "okay", "fine", "got it", "understand", "understood",
                        "thanks", "thank you", "ty", "thx", "cool", "noted",
                        "makes sense", "alright"],
        "weather":     ["weather", "forecast", "temperature", "raining", "sunny",
                        "cloudy", "outside"],
        "motivation":  ["motivate", "inspire", "motivation", "encourage", "quote",
                        "pep talk", "cheer me up", "i need motivation"],
        "compliment":  ["smart", "good bot", "nice", "great", "awesome", "well done",
                        "amazing", "love you", "you're great", "good job", "perfect"],
        "developer":   ["code", "bug", "developer", "program", "programming",
                        "software", "python", "javascript", "debugging", "coding"],
        "fact":        ["fact", "info", "information", "tell me something",
                        "did you know", "random fact", "fun fact"],
        "location":    ["where", "place", "live", "location", "where are you",
                        "where do you live"],
        "game":        ["game", "play", "mini game", "let's play", "wanna play"],
        "name":        ["your name", "who are you", "what are you", "what's your name",
                        "introduce yourself"],
        "help":        ["help", "what can you do", "commands", "what do you know",
                        "capabilities"],
        "age":         ["how old", "your age", "when were you born", "age"],
        "creator":     ["who made you", "who created you", "your creator",
                        "who built you", "who is your creator", "who is your developer"],
        "language":    ["what language", "built with", "coded in", "written in",
                        "what are you made of"],
        "hobby":       ["hobby", "hobbies", "what do you like", "what do you enjoy",
                        "your favorite", "favourite"],
        "sad":         ["i'm sad", "i am sad", "feeling sad", "i feel sad",
                        "depressed", "unhappy", "feeling down", "i feel down"],
        "happy":       ["i'm happy", "i am happy", "feeling happy", "great day",
                        "good day", "i feel good", "i'm doing great"],
        "bored":       ["i'm bored", "i am bored", "bored", "nothing to do",
                        "entertain me"],
        "insult":      ["stupid bot", "dumb bot", "you're useless", "you suck",
                        "hate you", "worst bot", "you're bad"],
    }

    # Words that suggest the user wants to calculate something inline
    CALC_TRIGGERS: list[str] = [
        "calculate", "calc", "what is", "what's", "solve", "compute", "evaluate",
    ]

    def __init__(
        self,
        responses_file: str = "responses.json",
        calculator: Calculator | None = None,
    ) -> None:
        self._responses_file      = responses_file
        self._responses: dict     = {}
        self._calculator          = calculator
        self._unknown_counter     = 0
        self._pending_teach_input = ""   # stores unrecognised input for teach flow

    # ── Persistence ────────────────────────────────────────────
    def load(self) -> bool:
        """Load responses.json. Returns True on success."""
        try:
            with open(self._responses_file, "r", encoding="utf-8") as f:
                self._responses = json.load(f)
            return True
        except FileNotFoundError:
            print(Fore.RED + "⚠️  responses.json not found.")
            return False

    def save(self) -> None:
        """Persist responses (including learned ones) back to disk."""
        with open(self._responses_file, "w", encoding="utf-8") as f:
            json.dump(self._responses, f, indent=2, ensure_ascii=False)

    # ── Core response logic ────────────────────────────────────
    def get_response(
        self,
        user_input: str,
        game_manager: GameManager | None = None,
    ) -> str:
        """
        Match *user_input* to an intent and return a response string.

        Priority order:
          1. Learned responses (exact match — highest priority)
          2. Inline calculator shortcut (natural language maths)
          3. Keyword intent matching (23 categories)
          4. Unknown handler (returns TEACH_PROMPT every 2nd miss)

        Special return values:
          TEACH_PROMPT  — caller must run the two-phase teaching flow.
          ""            — a game menu was already printed; GUI ignores.
        """
        text = user_input.lower().strip()

        # 1. Learned responses
        if text in self._responses.get("learned", {}):
            return random.choice(self._responses["learned"][text])

        # 2. Inline calculator shortcut
        if self._calculator:
            for trigger in self.CALC_TRIGGERS:
                if trigger in text:
                    expr = text.split(trigger, 1)[1].strip()
                    if expr:
                        return self._calculator.evaluate(expr)

        # 3. Keyword intent matching
        for category, keywords in self.TRIGGERS.items():
            if any(kw in text for kw in keywords):
                if category == "greeting":
                    return self._build_greeting()
                if category == "game" and game_manager:
                    game_manager.show_menu()
                    return ""
                response = random.choice(
                    self._responses.get(
                        category, self._responses.get("unknown", ["Hmm…"])
                    )
                )
                return self._format_dynamic(response)

        # 4. Unknown — signal teaching every 2nd miss
        self._unknown_counter += 1
        if self._unknown_counter % 2 == 0:
            self._pending_teach_input = text
            return TEACH_PROMPT

        return random.choice(
            self._responses.get("unknown", ["I didn't quite get that."])
        )

    def confirm_teach(self, wants_to_teach: bool, new_reply: str = "") -> str:
        """
        Phase-2 of the teaching flow.
        Called by the CLI or GUI after the user responds to TEACH_PROMPT.

        wants_to_teach : bool — did the user say yes?
        new_reply      : str  — the reply Cosmo should remember (if yes)
        Returns the message Cosmo should display.
        """
        if wants_to_teach and new_reply.strip():
            if "learned" not in self._responses:
                self._responses["learned"] = {}
            self._responses["learned"][self._pending_teach_input] = [new_reply.strip()]
            self.save()
            self._pending_teach_input = ""
            return "🧠 Got it! I'll remember that next time."
        self._pending_teach_input = ""
        return random.choice(
            self._responses.get("unknown", ["I didn't quite get that."])
        )

    # ── Internal helpers ───────────────────────────────────────
    def _build_greeting(self) -> str:
        hour = datetime.datetime.now().hour
        part = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
        base = random.choice(self._responses.get("greeting", ["Hey!"]))
        return f"{part}! {base}"

    @staticmethod
    def _format_dynamic(response: str) -> str:
        """Replace {time}, {date}, {weekday} placeholders with live values."""
        if "{time}" in response:
            return response.format(time=datetime.datetime.now().strftime("%H:%M"))
        if "{date}" in response or "{weekday}" in response:
            today = datetime.date.today()
            return response.format(
                date=today.strftime("%B %d, %Y"),
                weekday=today.strftime("%A"),
            )
        return response

    # ── Properties ─────────────────────────────────────────────
    @property
    def responses(self) -> dict:
        return self._responses

    @property
    def pending_teach_input(self) -> str:
        return self._pending_teach_input


# ══════════════════════════════════════════════════════════════
#  CommandHandler
# ══════════════════════════════════════════════════════════════
class CommandHandler:
    """
    Parses !-prefixed commands and routes each one to the correct
    sub-system. Always returns a plain string — never None —
    so the GUI can display it directly without any extra checks.
    """

    def __init__(
        self,
        theme_manager:   ThemeManager,
        calculator:      Calculator,
        game_manager:    GameManager,
        logger:          Logger,
        user_profile:    UserProfile,
        response_engine: ResponseEngine,
    ) -> None:
        self._theme   = theme_manager
        self._calc    = calculator
        self._games   = game_manager
        self._logger  = logger
        self._profile = user_profile
        self._engine  = response_engine

    # ── Parsing ────────────────────────────────────────────────
    @staticmethod
    def parse(user_input: str) -> tuple[bool, str, str]:
        """
        Detect and split a command starting with ! or /.
        Returns (is_command, command_name, args_string).
        """
        stripped = user_input.strip()
        if stripped.startswith("!") or stripped.startswith("/"):
            parts   = stripped[1:].split(maxsplit=1)
            command = parts[0].lower()
            args    = parts[1] if len(parts) > 1 else ""
            return True, command, args
        return False, "", ""

    # ── Execution ──────────────────────────────────────────────
    def execute(self, command: str, args: str) -> tuple[bool, str]:
        """
        Execute *command* with *args*.
        Returns (continue_chat: bool, response_string: str).
        Always returns a string — never None.
        """
        match command:
            case "help":
                return True, self.get_help_text()
            case "clear":
                self._clear_screen_cli()
                return True, "✨ Screen cleared!"
            case "history":
                return True, self.get_history_text(args)
            case "stats":
                return True, self.get_stats_text()
            case "reset":
                exited = self._reset_profile_cli()
                msg    = "✅ Profile reset! Restart Cosmo." if exited else "❌ Reset cancelled."
                return not exited, msg
            case "theme":
                name = args.strip().lower()
                if not name or name == "list":
                    return True, self._theme.list_themes_plain()
                return True, self._theme.apply(args)
            case "calc":
                return True, self._calc.evaluate(args)
            case "game":
                self._games.dispatch(args)   # CLI: blocking; GUI: uses GameSession
                return True, ""
            case _:
                return True, f"❓ Unknown command: !{command}. Type !help for options."

    # ── Pure-string display helpers (CLI + GUI share these) ────
    def get_help_text(self) -> str:
        """Return full help text as a plain string — no ANSI codes."""
        return (
            "📖 AVAILABLE COMMANDS\n"
            "─────────────────────────────────────\n"
            "🎨 Customisation:\n"
            "  !theme <n>         — Change colour theme\n"
            "  !theme list        — List all available themes\n\n"
            "🎮 Games & Fun:\n"
            "  !game              — Show game picker\n"
            "  !game <number>     — Launch game by number (1–4)\n"
            "  !game <name>       — Launch game by name keyword\n\n"
            "🔧 Utilities:\n"
            "  !calc <expression> — Evaluate a math expression\n"
            "  !history [n]       — View last n chat exchanges (default 10)\n"
            "  !clear             — Clear the chat screen\n\n"
            "📊 Information:\n"
            "  !stats             — Show message count statistics\n"
            "  !help              — Show this help menu\n\n"
            "⚙️  System:\n"
            "  !reset             — Reset your saved profile\n"
            "  bye / quit / exit  — End the chat session"
        )

    def get_history_text(self, args: str = "") -> str:
        """Return recent chat history as a plain string."""
        try:
            limit = int(args.strip()) if args.strip().isdigit() else 10
        except Exception:
            limit = 10
        lines = self._logger.read(limit)
        if not lines:
            return "📭 No chat history found yet."
        return "📜 Recent chat history:\n\n" + "\n".join(l.strip() for l in lines)

    def get_stats_text(self) -> str:
        """Return message count statistics as a plain string."""
        s = self._logger.stats()
        if s["total"] == 0:
            return "📭 No chat data available yet."
        return (
            f"📊 Chat Statistics:\n"
            f"   Total messages  : {s['total']}\n"
            f"   Your messages   : {s['user']}\n"
            f"   Cosmo's replies : {s['bot']}"
        )

    # ── CLI-only side-effect helpers ───────────────────────────
    def _clear_screen_cli(self) -> None:
        os.system("cls" if os.name == "nt" else "clear")
        from bot import CosmoBot          # local import avoids circular dependency
        CosmoBot.print_banner(self._theme)
        print(Fore.GREEN + "✨ Screen cleared!\n")

    def _reset_profile_cli(self) -> bool:
        confirm = input(
            Fore.YELLOW + "⚠️  Reset your profile? (yes/no): "
        ).strip().lower()
        if confirm in ("yes", "y"):
            self._profile.reset()
            print(Fore.GREEN + "✅ Profile reset! Restart Cosmo to create a new profile.")
            return True
        print(Fore.CYAN + "❌ Reset cancelled.")
        return False
