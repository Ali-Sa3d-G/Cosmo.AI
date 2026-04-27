"""
bot.py
──────
CosmoBot — the top-level orchestrator that wires every module
together and provides two clean entry points:

  CLI  → bot.start()
             Loads state, prints the banner, greets the user,
             then blocks in _loop() until the user says goodbye.

  GUI  → bot.boot()  then  bot.process_message(text)
             boot() loads all persistent state (no I/O at all).
             process_message() handles one message per call and
             returns (response_string, session_ended) so Tkinter's
             mainloop() stays in full control of the thread.

Module wiring (what imports what)
──────────────────────────────────
  bot.py
    ← theme.py    (ThemeManager)
    ← memory.py   (Logger, MessageHistory, UserProfile)
    ← brain.py    (Calculator, ResponseEngine, CommandHandler,
                   TEACH_PROMPT)
    ← games.py    (GameManager, GameSession)
"""

from __future__ import annotations

import random
import time

from colorama import Fore, Style

from brain  import Calculator, CommandHandler, ResponseEngine, TEACH_PROMPT
from games  import GameManager, GameSession
from memory import Logger, MessageHistory, UserProfile
from theme  import ThemeManager


class CosmoBot:
    """
    Top-level orchestrator.
    CLI  → start()
    GUI  → boot()  +  process_message()
    """

    EXIT_WORDS: frozenset[str] = frozenset({"bye", "quit", "exit"})

    def __init__(
        self,
        responses_file: str = "responses.json",
        user_data_file: str = "user_data.json",
        log_file:       str = "chat_log.txt",
    ) -> None:
        # ── Build and wire every sub-system ───────────────────
        self._theme   = ThemeManager(data_file=user_data_file)
        self._logger  = Logger(log_file=log_file)
        self._history = MessageHistory()
        self._profile = UserProfile(data_file=user_data_file)
        self._calc    = Calculator()
        self._engine  = ResponseEngine(
            responses_file=responses_file,
            calculator=self._calc,
        )
        self._games   = GameManager(theme_manager=self._theme)
        self._session = GameSession()
        self._cmds    = CommandHandler(
            theme_manager   = self._theme,
            calculator      = self._calc,
            game_manager    = self._games,
            logger          = self._logger,
            user_profile    = self._profile,
            response_engine = self._engine,
        )
        self._user_name: str = ""

    # ══════════════════════════════════════════════════════════
    #  Shared initialisation (CLI + GUI)
    # ══════════════════════════════════════════════════════════
    def boot(self) -> None:
        """
        Load all persistent state from disk.
        No I/O side-effects — safe to call before start() or
        process_message(). Call this once before anything else.
        """
        self._theme.load()
        self._engine.load()
        self._profile.load()

    # ══════════════════════════════════════════════════════════
    #  GUI entry points
    # ══════════════════════════════════════════════════════════
    def initialize_user(self, name: str) -> str:
        """
        GUI: register a name from the onboarding dialog.
        Returns the cleaned, capitalised name.
        """
        self._user_name = self._profile.register(name)
        return self._user_name

    def process_message(self, user_input: str) -> tuple[str, bool]:
        """
        GUI: handle one user message, return (response, session_ended).

        response      — string for the GUI to display;
                        if equal to TEACH_PROMPT, the GUI must show
                        a teaching dialog and later call teach_confirm().
        session_ended — True when the user typed bye / quit / exit.
        """
        text = user_input.strip()
        if not text:
            return "", False

        self._logger.log(self._user_name, text)
        self._history.add(self._user_name, text)

        # Exit?
        if text.lower() in self.EXIT_WORDS:
            farewell = random.choice(
                self._engine.responses.get("farewell", ["Goodbye!"])
            )
            self._logger.log("Cosmo", farewell)
            self._history.add("Cosmo", farewell)
            return farewell, True

        # Command?
        is_cmd, command, args = CommandHandler.parse(text)
        if is_cmd:
            continue_chat, msg = self._cmds.execute(command, args)
            if msg:
                self._logger.log("Cosmo", msg)
                self._history.add("Cosmo", msg)
            return msg, not continue_chat

        # Normal conversation
        response = self._engine.get_response(text, self._games)
        if response and response != TEACH_PROMPT:
            self._logger.log("Cosmo", response)
            self._history.add("Cosmo", response)
        return response, False

    def teach_confirm(self, wants_to_teach: bool, new_reply: str = "") -> str:
        """
        GUI: complete the two-phase teaching flow.
        Call this after the user responds to a TEACH_PROMPT.
        """
        msg = self._engine.confirm_teach(wants_to_teach, new_reply)
        self._logger.log("Cosmo", msg)
        self._history.add("Cosmo", msg)
        return msg

    # ══════════════════════════════════════════════════════════
    #  CLI entry points
    # ══════════════════════════════════════════════════════════
    def start(self) -> None:
        """CLI: full blocking startup → boot → banner → greet → loop."""
        self.boot()
        self.print_banner(self._theme)
        p = self._theme.color("primary")
        print(p + "🤖 Cosmo: Hello! I'm Cosmo, your chat buddy with personality!")
        print(p + "Type 'bye', 'quit', or 'exit' to end the chat.\n")
        if not self._engine.responses:
            print(Fore.RED + "⚠️  Could not load responses.json. Exiting.")
            return
        self._user_name = self._profile.greet_or_register(self._theme)
        print(self._theme.color("primary") + f"🤖 Cosmo: How can I help you today, {self._user_name}?\n")
        self._loop()

    def _loop(self) -> None:
        """CLI: blocking main conversation loop."""
        teach_pending = False

        while True:
            prompt = (
                Fore.YELLOW + "Teach me (type reply or 'no'): "
                if teach_pending else
                Fore.GREEN  + f"{self._user_name}: "
            )
            user_input = input(prompt + Style.RESET_ALL).strip()
            if not user_input:
                continue

            # Teaching phase
            if teach_pending:
                teach_pending = False
                if user_input.lower() in ("no", "n", "nope"):
                    response = self._engine.confirm_teach(False)
                else:
                    response = self._engine.confirm_teach(True, user_input)
                self._typing_effect(f"🤖 Cosmo: {response}")
                self._logger.log("Cosmo", response)
                continue

            self._logger.log(self._user_name, user_input)

            # Exit
            if user_input.lower() in self.EXIT_WORDS:
                farewell = random.choice(
                    self._engine.responses.get("farewell", ["Goodbye!"])
                )
                self._typing_effect(f"🤖 Cosmo: {farewell}")
                self._logger.log("Cosmo", farewell)
                break

            # Command
            is_cmd, command, args = CommandHandler.parse(user_input)
            if is_cmd:
                continue_chat, msg = self._cmds.execute(command, args)
                if msg:
                    self._typing_effect(f"🤖 Cosmo: {msg}")
                    self._logger.log("Cosmo", msg)
                if not continue_chat:
                    break
                continue

            # Normal conversation
            response = self._engine.get_response(user_input, self._games)
            if response == TEACH_PROMPT:
                self._typing_effect(
                    "🤖 Cosmo: I don't know that one. "
                    "Would you like to teach me? Type your reply or 'no':"
                )
                teach_pending = True
                continue
            if response:
                self._typing_effect(f"🤖 Cosmo: {response}")
                self._logger.log("Cosmo", response)

    # ══════════════════════════════════════════════════════════
    #  Helpers
    # ══════════════════════════════════════════════════════════
    def _typing_effect(self, text: str, delay: float = 0.03) -> None:
        colored = self._theme.color("primary") + text
        for char in colored:
            print(char, end="", flush=True)
            time.sleep(delay)
        print(Style.RESET_ALL)

    @staticmethod
    def print_banner(theme: ThemeManager) -> None:
        """Print the ASCII-art banner in the active theme colour."""
        banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║        ██████╗ ██████╗ ███████╗███╗   ███╗ ██████╗        ║
    ║       ██╔════╝██╔═══██╗██╔════╝████╗ ████║██╔═══██╗       ║
    ║       ██║     ██║   ██║███████╗██╔████╔██║██║   ██║       ║
    ║       ██║     ██║   ██║╚════██║██║╚██╔╝██║██║   ██║       ║
    ║       ╚██████╗╚██████╔╝███████║██║ ╚═╝ ██║╚██████╔╝       ║
    ║        ╚═════╝ ╚═════╝ ╚══════╝╚═╝     ╚═╝ ╚═════╝        ║
    ║                                                           ║
    ║          🤖 Your AI Chat Buddy with Personality 🤖       ║
    ║               Version 3.1 — GUI-Ready OOP Edition         ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
        print(theme.color("primary") + Style.BRIGHT + banner)
        print(Fore.YELLOW + "    💡 Type '!help' to see all available commands")
        print(Fore.YELLOW + "    🎨 Type '!theme <n>' to change colours")
        print(Fore.YELLOW + "    🎮 Type '!game' to play mini-games\n")

    # ══════════════════════════════════════════════════════════
    #  GUI convenience properties
    # ══════════════════════════════════════════════════════════
    @property
    def theme(self)     -> ThemeManager:   return self._theme
    @property
    def profile(self)   -> UserProfile:    return self._profile
    @property
    def history(self)   -> MessageHistory: return self._history
    @property
    def games(self)     -> GameManager:    return self._games
    @property
    def session(self)   -> GameSession:    return self._session
    @property
    def user_name(self) -> str:            return self._user_name
