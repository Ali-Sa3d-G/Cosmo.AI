"""
theme.py
────────
ThemeManager — owns the complete colour catalogue for Cosmo.

Every theme contains two colour representations side by side:
  • ANSI codes  → used by the CLI  (colorama / print)
  • Hex strings → used by the GUI  (Tkinter widgets)

This means neither the CLI nor the GUI needs to convert or
know about the other's colour format. They each just call
the accessor they need:
  theme.color("primary")      → ANSI escape string  (CLI)
  theme.hex_color("primary")  → "#RRGGBB" string    (GUI)

Available colour slots
──────────────────────
  primary | secondary | accent | name     (ANSI side)
  primary | secondary | accent |          (hex side, key prefix "hex_")
  bg | text | user_msg | bot_msg

Public API
──────────
  load()                  — read saved theme from user_data.json
  save(name)              — write theme name to user_data.json
  apply(name)   → str     — switch + save + return status message
  color(slot)   → str     — ANSI colour code  (CLI)
  hex_color(slot) → str   — hex colour string (GUI)
  list_themes() → str     — ANSI listing      (CLI)
  list_themes_plain() → str — plain listing   (GUI)
  current_name  → str     — key of active theme
  all_names     → list    — all theme key names
"""

import json
import os

from colorama import Fore, Style


class ThemeManager:
    """Manages colour themes for both the CLI (ANSI) and GUI (hex)."""

    THEMES: dict[str, dict] = {
        "cyan": {
            # ── CLI ────────────────────────────────────────────
            "primary":       Fore.CYAN,
            "secondary":     Fore.LIGHTCYAN_EX,
            "accent":        Fore.BLUE,
            "name":          "Ocean Blue",
            # ── GUI ────────────────────────────────────────────
            "hex_primary":   "#00FFFF",
            "hex_secondary": "#E0FFFF",
            "hex_accent":    "#4A90D9",
            "hex_bg":        "#0D1117",
            "hex_text":      "#E6EDF3",
            "hex_user_msg":  "#1F6FEB",
            "hex_bot_msg":   "#161B22",
        },
        "green": {
            "primary":       Fore.GREEN,
            "secondary":     Fore.LIGHTGREEN_EX,
            "accent":        Fore.LIGHTGREEN_EX,
            "name":          "Matrix Green",
            "hex_primary":   "#00FF41",
            "hex_secondary": "#CCFFCC",
            "hex_accent":    "#39FF14",
            "hex_bg":        "#0A0F0A",
            "hex_text":      "#E6EDF3",
            "hex_user_msg":  "#1A5C2A",
            "hex_bot_msg":   "#0F1F0F",
        },
        "magenta": {
            "primary":       Fore.MAGENTA,
            "secondary":     Fore.LIGHTMAGENTA_EX,
            "accent":        Fore.MAGENTA,
            "name":          "Purple Dream",
            "hex_primary":   "#FF00FF",
            "hex_secondary": "#FFB3FF",
            "hex_accent":    "#BF5FFF",
            "hex_bg":        "#110D1A",
            "hex_text":      "#F0E6FF",
            "hex_user_msg":  "#6A0DAD",
            "hex_bot_msg":   "#1A1025",
        },
        "yellow": {
            "primary":       Fore.YELLOW,
            "secondary":     Fore.LIGHTYELLOW_EX,
            "accent":        Fore.YELLOW,
            "name":          "Sunshine Yellow",
            "hex_primary":   "#FFD700",
            "hex_secondary": "#FFFACD",
            "hex_accent":    "#FFA500",
            "hex_bg":        "#1A1600",
            "hex_text":      "#FFF8DC",
            "hex_user_msg":  "#8B7000",
            "hex_bot_msg":   "#1F1C00",
        },
        "red": {
            "primary":       Fore.RED,
            "secondary":     Fore.LIGHTRED_EX,
            "accent":        Fore.RED,
            "name":          "Ruby Red",
            "hex_primary":   "#FF3B3B",
            "hex_secondary": "#FFB3B3",
            "hex_accent":    "#CC0000",
            "hex_bg":        "#1A0000",
            "hex_text":      "#FFE6E6",
            "hex_user_msg":  "#8B0000",
            "hex_bot_msg":   "#1F0000",
        },
    }

    def __init__(self, data_file: str = "user_data.json") -> None:
        self._data_file     = data_file
        self._current_theme = self.THEMES["cyan"]

    # ── Persistence ────────────────────────────────────────────
    def load(self) -> None:
        """Load the saved theme name from disk and apply it."""
        if os.path.exists(self._data_file):
            try:
                with open(self._data_file, "r") as f:
                    data = json.load(f)
                name = data.get("theme", "cyan")
                self._current_theme = self.THEMES.get(name, self.THEMES["cyan"])
            except Exception:
                self._current_theme = self.THEMES["cyan"]

    def save(self, theme_name: str) -> None:
        """Write the theme name to disk without overwriting other keys."""
        data: dict = {}
        if os.path.exists(self._data_file):
            try:
                with open(self._data_file, "r") as f:
                    data = json.load(f)
            except Exception:
                pass
        data["theme"] = theme_name
        with open(self._data_file, "w") as f:
            json.dump(data, f, indent=2)

    def apply(self, theme_name: str) -> str:
        """Switch to *theme_name*, persist it, return a status message."""
        name = theme_name.strip().lower()
        if name in self.THEMES:
            self._current_theme = self.THEMES[name]
            self.save(name)
            return f"✨ Theme changed to {self.THEMES[name]['name']}!"
        return f"❓ Theme '{name}' not found. Use !theme list to see options."

    # ── Colour accessors ───────────────────────────────────────
    def color(self, slot: str = "primary") -> str:
        """Return the ANSI escape code for *slot* (CLI use)."""
        return self._current_theme.get(slot, Fore.CYAN)

    def hex_color(self, slot: str = "primary") -> str:
        """Return the hex colour string for *slot* (Tkinter use)."""
        return self._current_theme.get(f"hex_{slot}", "#00FFFF")

    # ── Theme listing ──────────────────────────────────────────
    def list_themes(self) -> str:
        """ANSI-coloured listing — for the CLI."""
        lines = ["\n🎨 Available themes:\n"]
        for key, theme in self.THEMES.items():
            marker = "→" if theme == self._current_theme else " "
            lines.append(
                f"  {marker} {theme['primary']}{key}{Style.RESET_ALL}"
                f" — {theme['name']}"
            )
        lines.append("\nUse: !theme <name> to switch")
        return "\n".join(lines)

    def list_themes_plain(self) -> str:
        """Plain-text listing — no ANSI codes, safe for Tkinter labels."""
        lines = ["🎨 Available themes:\n"]
        for key, theme in self.THEMES.items():
            marker = "→" if theme == self._current_theme else " "
            lines.append(f"  {marker} {key} — {theme['name']}")
        lines.append("\nUse: !theme <name> to switch")
        return "\n".join(lines)

    # ── Properties ─────────────────────────────────────────────
    @property
    def current_name(self) -> str:
        """Key string of the active theme (e.g. 'cyan')."""
        for key, val in self.THEMES.items():
            if val == self._current_theme:
                return key
        return "cyan"

    @property
    def all_names(self) -> list[str]:
        """All theme key names — useful for GUI dropdowns."""
        return list(self.THEMES.keys())
