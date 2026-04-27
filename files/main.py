"""
main.py
───────
Cosmo v3.1 — GUI-Ready OOP Edition
Author: Ali Saad

Entry point for the CLI version.
Run with:
    python main.py

The GUI version will have its own entry point (gui.py) that calls
    bot = CosmoBot()
    bot.boot()
and then wraps bot.process_message() in a Tkinter window.
"""

from bot import CosmoBot


def main() -> None:
    bot = CosmoBot()
    bot.start()


if __name__ == "__main__":
    main()
