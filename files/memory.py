"""
memory.py
─────────
Everything Cosmo uses to remember things — past, present, and
who it's talking to.  Three classes, one clear theme:

  Logger          — long-term memory (disk)
                    Appends every message to chat_log.txt with
                    a timestamp. Provides read-back and stats
                    for !history and !stats commands.

  MessageHistory  — short-term memory (RAM)
                    Keeps the current session's messages in a
                    list so the GUI can populate its chat widget
                    without reading the log file. Lost on exit.

  UserProfile     — identity memory (disk)
                    Loads, saves, and resets the user's name and
                    theme preference stored in user_data.json.

    GUI API  → is_new_user()  +  register(raw_input)
                   Pure logic — no print() or input() at all.
                   The GUI provides the name from its dialog box.

    CLI API  → greet_or_register(theme_manager)
                   Handles I/O directly (input / print).
                   Calls is_new_user() + register() internally.
"""

from __future__ import annotations

import datetime
import json
import os
from typing import TYPE_CHECKING

from colorama import Fore, Style

if TYPE_CHECKING:
    from theme import ThemeManager


# ══════════════════════════════════════════════════════════════
#  Logger  —  long-term disk persistence
# ══════════════════════════════════════════════════════════════
class Logger:
    """Appends timestamped messages to chat_log.txt."""

    def __init__(self, log_file: str = "chat_log.txt") -> None:
        self._log_file = log_file

    def log(self, speaker: str, message: str) -> None:
        """Append one line: [YYYY-MM-DD HH:MM:SS] Speaker: text"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self._log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {speaker}: {message}\n")

    def read(self, limit: int = 10) -> list[str]:
        """
        Return the last *limit* exchanges from the log.
        One exchange = 2 lines (user + bot reply).
        """
        if not os.path.exists(self._log_file):
            return []
        with open(self._log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return lines[-(limit * 2):] if len(lines) > limit * 2 else lines

    def stats(self) -> dict[str, int]:
        """Return {"total": n, "user": n, "bot": n} message counts."""
        if not os.path.exists(self._log_file):
            return {"total": 0, "user": 0, "bot": 0}
        with open(self._log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        bot  = [l for l in lines if "Cosmo:" in l]
        user = [l for l in lines if "Cosmo:" not in l]
        return {"total": len(lines), "user": len(user), "bot": len(bot)}


# ══════════════════════════════════════════════════════════════
#  MessageHistory  —  short-term RAM buffer
# ══════════════════════════════════════════════════════════════
class MessageHistory:
    """
    In-memory list of the current session's messages.
    Each entry: {"sender": str, "text": str, "timestamp": "HH:MM"}
    Used by the GUI to populate and refresh its chat widget.
    """

    def __init__(self) -> None:
        self._messages: list[dict] = []

    def add(self, sender: str, text: str) -> None:
        """Append one message to the buffer."""
        ts = datetime.datetime.now().strftime("%H:%M")
        self._messages.append({"sender": sender, "text": text, "timestamp": ts})

    def get_all(self) -> list[dict]:
        """Return a shallow copy of all stored messages."""
        return list(self._messages)

    def clear(self) -> None:
        """Wipe all messages (e.g. on profile reset)."""
        self._messages.clear()

    def __len__(self) -> int:
        return len(self._messages)


# ══════════════════════════════════════════════════════════════
#  UserProfile  —  who is Cosmo talking to?
# ══════════════════════════════════════════════════════════════
class UserProfile:
    """Loads, saves, and resets the user's name and theme preference."""

    def __init__(self, data_file: str = "user_data.json") -> None:
        self._data_file = data_file
        self._data: dict = {}

    # ── Persistence ────────────────────────────────────────────
    def load(self) -> dict:
        """Load user_data.json. Returns {} if the file is missing."""
        if os.path.exists(self._data_file):
            try:
                with open(self._data_file, "r") as f:
                    self._data = json.load(f)
            except Exception:
                self._data = {}
        return self._data

    def save(self) -> None:
        """Write the current data dict back to disk."""
        with open(self._data_file, "w") as f:
            json.dump(self._data, f, indent=2)

    def reset(self) -> None:
        """Delete the data file and clear in-memory state."""
        if os.path.exists(self._data_file):
            os.remove(self._data_file)
        self._data = {}

    # ── GUI API — pure logic, no I/O ──────────────────────────
    def is_new_user(self) -> bool:
        """
        True if no name has been saved yet.
        Re-reads the file first so it always reflects disk state.
        The GUI calls this to decide whether to show an onboarding dialog.
        """
        self.load()
        return "name" not in self._data

    def register(self, raw_input: str) -> str:
        """
        Clean *raw_input*, save it as the user's name, return it.
        Strips natural-language prefixes:
            "my name is ali" → "Ali"
            "i am sara"      → "Sara"
            "i'm john"       → "John"
        Falls back to "Friend" if the result is empty.
        """
        text = raw_input.strip()
        for prefix in ["my name is", "i am", "i'm"]:
            if text.lower().startswith(prefix):
                text = text[len(prefix):].strip()
                break
        name = text.capitalize() or "Friend"
        self._data["name"] = name
        self.save()
        return name

    # ── CLI API — handles I/O directly ────────────────────────
    def greet_or_register(self, theme_manager: ThemeManager) -> str:
        """
        CLI helper: welcome returning users or prompt new ones.
        Internally calls is_new_user() + register().
        """
        if not self.is_new_user():
            print(Fore.CYAN + f"🤖 Cosmo: Welcome back, {self._data['name']}!")
            return self._data["name"]
        raw  = input(
            theme_manager.color("primary")
            + "🤖 Cosmo: What's your name? "
            + Style.RESET_ALL
        ).strip()
        name = self.register(raw)
        print(Fore.CYAN + f"🤖 Cosmo: Nice to meet you, {name}!")
        return name

    # ── Property ───────────────────────────────────────────────
    @property
    def name(self) -> str:
        return self._data.get("name", "Friend")
