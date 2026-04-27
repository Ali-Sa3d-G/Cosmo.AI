"""
games.py
────────
Everything related to Cosmo's mini-games — seven classes,
all in one place, grouped top-to-bottom in dependency order:

  BaseGame        — Abstract Base Class.  Defines the contract
                    every game must follow and provides shared
                    helpers (_say, _score_feedback, etc.).

  GuessingGame    — Guess Cosmo's secret number (1–10).
  TriviaGame      — 5 multiple-choice tech trivia questions.
  WordScramble    — Unscramble 5 tech-themed words.
  MathChallenge   — Solve 5 randomly generated arithmetic problems.

  GameSession     — Tracks one active game for the GUI and routes
                    each submitted answer to the right game object.
                    (The CLI calls game.play() directly instead.)

  GameManager     — Registry and dispatcher. Holds the list of
                    registered games, builds menus, and runs the
                    correct game when the user types !game.

Two APIs per game
─────────────────
  CLI  → game.play()
             Blocking loop — uses input() and print() directly.

  GUI  → game.start_game()  then  game.submit_answer(text)
             Non-blocking state-machine — returns plain dicts so
             the GUI can render them without blocking Tkinter.

Dict contract (GUI)
────────────────────
  start_game() and non-final submit_answer() return:
    {"message": str, "prompt": str, "done": False}

  Final submit_answer() (game over) returns:
    {"message": str, "prompt": "", "done": True, "score": str}
"""

from __future__ import annotations

import random
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from colorama import Fore, Style

if TYPE_CHECKING:
    from theme import ThemeManager


# ══════════════════════════════════════════════════════════════
#  BaseGame  —  Abstract Base Class
# ══════════════════════════════════════════════════════════════
class BaseGame(ABC):
    """Abstract base for all Cosmo mini-games."""

    def __init__(self, theme_manager: ThemeManager) -> None:
        self._theme = theme_manager

    # ── Abstract contract (every game must implement these) ───
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @abstractmethod
    def play(self) -> None:
        """CLI: run the full blocking game loop."""
        ...

    @abstractmethod
    def start_game(self) -> dict:
        """GUI: initialise state and return the opening dict."""
        ...

    @abstractmethod
    def submit_answer(self, user_input: str) -> dict:
        """GUI: process one answer and return the updated state dict."""
        ...

    # ── Shared helpers (inherited by all four games) ───────────
    def _say(self, message: str, delay: float = 0.03) -> None:
        """Print *message* character-by-character in theme colour (CLI)."""
        text = self._theme.color("primary") + message
        for char in text:
            print(char, end="", flush=True)
            time.sleep(delay)
        print(Style.RESET_ALL)

    def _primary(self, text: str) -> str:
        """Wrap *text* in the theme's primary ANSI colour (CLI)."""
        return self._theme.color("primary") + text + Style.RESET_ALL

    def _score_feedback(self, score: int, total: int) -> None:
        """Print a performance rating message (CLI)."""
        self._say(self._score_feedback_text(score, total))

    @staticmethod
    def _score_feedback_text(score: int, total: int) -> str:
        """Return a performance rating string (used by CLI + GUI)."""
        ratio = score / total if total else 0
        if ratio == 1.0:  return "🏆 Perfect score! Incredible!"
        if ratio >= 0.7:  return "🌟 Great job!"
        if ratio >= 0.5:  return "👍 Not bad! Keep it up."
        return "📚 Keep practicing — you'll improve!"


# ══════════════════════════════════════════════════════════════
#  GuessingGame
# ══════════════════════════════════════════════════════════════
class GuessingGame(BaseGame):
    """Guess Cosmo's secret number between 1 and 10."""

    def __init__(self, theme_manager: ThemeManager) -> None:
        super().__init__(theme_manager)
        self._secret:   int  = 0
        self._attempts: int  = 0
        self._active:   bool = False

    @property
    def name(self) -> str:        return "Number Guessing"
    @property
    def description(self) -> str: return "Guess the secret number between 1 and 10!"

    # ── CLI ────────────────────────────────────────────────────
    def play(self) -> None:
        self._say("🎮 Let's play NUMBER GUESSING (1–10)!")
        secret, attempts = random.randint(1, 10), 0
        while True:
            raw = input(Fore.GREEN + "Your guess: " + Style.RESET_ALL).strip()
            if raw.lower() in ("quit", "exit", "stop"):
                self._say(f"🤖 The number was {secret}. Better luck next time!")
                return
            try:
                guess = int(raw); attempts += 1
                if not 1 <= guess <= 10:
                    self._say("🤖 Please enter a number between 1 and 10!")
                elif guess == secret:
                    self._say(f"🎉 You got it in {attempts} attempt(s)! That was fun!")
                    return
                else:
                    self._say("🤖 Too low! Try again." if guess < secret else "🤖 Too high! Try again.")
            except ValueError:
                self._say("🤖 Please enter a valid number!")

    # ── GUI ────────────────────────────────────────────────────
    def start_game(self) -> dict:
        self._secret   = random.randint(1, 10)
        self._attempts = 0
        self._active   = True
        return {
            "message": (
                "\U0001f3ae Let's play NUMBER GUESSING!\n\n"
                "I'm thinking of a number between 1 and 10.\n"
                "Can you guess it?"
            ),
            "prompt":  "Enter your guess (1\u201310):",
            "done":    False,
        }

    def submit_answer(self, user_input: str) -> dict:
        raw = user_input.strip()
        if raw.lower() in ("quit", "exit", "stop"):
            self._active = False
            return {
                "message": f"You quit! The number was {self._secret}. Better luck next time! 🙂",
                "prompt":  "", "done": True,
                "score":   f"Quit after {self._attempts} attempt(s)",
            }
        try:
            guess = int(raw)
        except ValueError:
            return {
                "message": "⚠️  That's not a valid number. Try again!",
                "prompt":  "Enter your guess (1–10):", "done": False,
            }
        self._attempts += 1
        if not 1 <= guess <= 10:
            return {
                "message": "⚠️  Please enter a number between 1 and 10!",
                "prompt":  "Enter your guess (1–10):", "done": False,
            }
        if guess == self._secret:
            self._active = False
            return {
                "message": f"🎉 You got it in {self._attempts} attempt(s)! That was fun!",
                "prompt":  "", "done": True,
                "score":   f"Solved in {self._attempts} attempt(s)",
            }
        hint = "📉 Too low! Try a higher number." if guess < self._secret else "📈 Too high! Try a lower number."
        return {"message": hint, "prompt": "Enter your guess (1–10):", "done": False}


# ══════════════════════════════════════════════════════════════
#  TriviaGame
# ══════════════════════════════════════════════════════════════
class TriviaGame(BaseGame):
    """5 multiple-choice technology trivia questions."""

    QUESTIONS: list[dict] = [
        {"question": "What does CPU stand for?",
         "options":  ["A) Central Processing Unit", "B) Computer Personal Unit", "C) Central Program Utility", "D) Core Processing Unit"],
         "answer": "A"},
        {"question": "Which language is called the 'language of the web'?",
         "options":  ["A) Python", "B) Java", "C) JavaScript", "D) C++"],
         "answer": "C"},
        {"question": "What year was Python first released?",
         "options":  ["A) 1989", "B) 1991", "C) 1995", "D) 2000"],
         "answer": "B"},
        {"question": "What does HTML stand for?",
         "options":  ["A) Hyperlinks and Text Markup Language", "B) HyperText Markup Language", "C) Home Tool Markup Language", "D) Hyperlinking Text Marking Language"],
         "answer": "B"},
        {"question": "Who is known as the father of computers?",
         "options":  ["A) Bill Gates", "B) Steve Jobs", "C) Charles Babbage", "D) Alan Turing"],
         "answer": "C"},
    ]

    def __init__(self, theme_manager: ThemeManager) -> None:
        super().__init__(theme_manager)
        self._index: int = 0
        self._score: int = 0

    @property
    def name(self) -> str:        return "Trivia Quiz"
    @property
    def description(self) -> str: return "Test your tech knowledge!"

    # ── CLI ────────────────────────────────────────────────────
    def play(self) -> None:
        self._say("🎮 Let's play TRIVIA!")
        score = 0
        for i, q in enumerate(self.QUESTIONS, 1):
            q_text = q["question"]
            print(f"\n{self._primary(f'Question {i}/{len(self.QUESTIONS)}: {q_text}')}")
            for opt in q["options"]:
                print(Fore.WHITE + f"  {opt}")
            answer = input(Fore.GREEN + "Your answer (A/B/C/D): " + Style.RESET_ALL).strip().upper()
            if answer == q["answer"]:
                self._say("✅ Correct!"); score += 1
            else:
                self._say(f"❌ Wrong! Correct answer: {q['answer']}")
        print(f"\n{self._primary(f'🎯 Final Score: {score}/{len(self.QUESTIONS)}')}")
        self._score_feedback(score, len(self.QUESTIONS))

    # ── GUI ────────────────────────────────────────────────────
    def start_game(self) -> dict:
        self._index = 0; self._score = 0
        return self._question_dict()

    def submit_answer(self, user_input: str) -> dict:
        q       = self.QUESTIONS[self._index]
        correct = user_input.strip().upper() == q["answer"]
        if correct: self._score += 1
        feedback = "✅ Correct!" if correct else f"❌ Wrong! Correct answer: {q['answer']}"
        self._index += 1
        if self._index >= len(self.QUESTIONS):
            fb = self._score_feedback_text(self._score, len(self.QUESTIONS))
            return {"message": f"{feedback}\n\n🎯 Final Score: {self._score}/{len(self.QUESTIONS)}\n{fb}", "prompt": "", "done": True, "score": f"{self._score}/{len(self.QUESTIONS)}"}
        nq = self._question_dict()
        combined_message = f"{feedback}\n\n{nq['message']}"
        return {"message": combined_message, "prompt": nq["prompt"], "question_data": nq.get("question_data"), "done": False}

    def _question_dict(self) -> dict:
        q    = self.QUESTIONS[self._index]
        opts = "\n".join(f"  {o}" for o in q["options"])
        return {"message": f"Question {self._index+1}/{len(self.QUESTIONS)}: {q['question']}", "prompt": f"{opts}\nYour answer (A/B/C/D):", "question_data": q, "done": False}


# ══════════════════════════════════════════════════════════════
#  WordScramble
# ══════════════════════════════════════════════════════════════
class WordScramble(BaseGame):
    """Unscramble 5 tech-themed words with hints."""

    WORDS: list[dict] = [
        {"word": "python",    "hint": "A popular programming language (snake!)"},
        {"word": "computer",  "hint": "Electronic device for processing data"},
        {"word": "keyboard",  "hint": "Input device with keys"},
        {"word": "algorithm", "hint": "Step-by-step problem-solving procedure"},
        {"word": "database",  "hint": "Organised collection of data"},
    ]

    def __init__(self, theme_manager: ThemeManager) -> None:
        super().__init__(theme_manager)
        self._index:     int = 0
        self._score:     int = 0
        self._scrambled: str = ""

    @property
    def name(self) -> str:        return "Word Scramble"
    @property
    def description(self) -> str: return "Unscramble the tech words!"

    # ── CLI ────────────────────────────────────────────────────
    def play(self) -> None:
        self._say("🎮 Let's play WORD SCRAMBLE!")
        score = 0
        for i, item in enumerate(self.WORDS, 1):
            word = item["word"]; scrambled = self._scramble(word)
            print(f"\n{self._primary(f'Round {i}/{len(self.WORDS)}')}")
            print(Fore.YELLOW + f"Scrambled: {scrambled.upper()}")
            print(Fore.CYAN   + f"Hint: {item['hint']}")
            guess = input(Fore.GREEN + "Your answer: " + Style.RESET_ALL).strip().lower()
            if guess == word:
                self._say("✅ Correct!"); score += 1
            else:
                self._say(f"❌ Wrong! The answer was: {word}")
        print(f"\n{self._primary(f'🎯 Final Score: {score}/{len(self.WORDS)}')}")
        self._score_feedback(score, len(self.WORDS))

    # ── GUI ────────────────────────────────────────────────────
    def start_game(self) -> dict:
        self._index = 0; self._score = 0
        return self._round_dict()

    def submit_answer(self, user_input: str) -> dict:
        word    = self.WORDS[self._index]["word"]
        correct = user_input.strip().lower() == word
        if correct: self._score += 1
        feedback = "✅ Correct!" if correct else f"❌ Wrong! The answer was: {word}"
        self._index += 1
        if self._index >= len(self.WORDS):
            fb = self._score_feedback_text(self._score, len(self.WORDS))
            return {"message": f"{feedback}\n\n🎯 Final Score: {self._score}/{len(self.WORDS)}\n{fb}", "prompt": "", "done": True, "score": f"{self._score}/{len(self.WORDS)}"}
        nr = self._round_dict()
        return {
            "message": f"{feedback}\n\n{nr['message']}",
            "prompt":  nr["prompt"],
            "done":    False,
        }

    def _round_dict(self) -> dict:
        item            = self.WORDS[self._index]
        self._scrambled = self._scramble(item["word"])
        return {
            "message": (
                f"Round {self._index + 1}/{len(self.WORDS)}\n\n"
                f"Scrambled word:  {self._scrambled.upper()}\n"
                f"Hint:  {item['hint']}"
            ),
            "prompt": "Type the unscrambled word:",
            "done":   False,
        }
    @staticmethod
    def _scramble(word: str) -> str:
        """Return a scrambled version of *word*.
        Guaranteed to differ from the original (up to 200 attempts),
        falls back to the word reversed if all attempts produce the same."""
        if len(word) <= 1:
            return word
        for _ in range(200):
            s = "".join(random.sample(word, len(word)))
            if s != word:
                return s
        # Ultimate fallback: reverse the word
        return word[::-1]


# ══════════════════════════════════════════════════════════════
#  MathChallenge
# ══════════════════════════════════════════════════════════════
class MathChallenge(BaseGame):
    """5 rounds of randomly generated arithmetic."""

    TOTAL: int = 5

    def __init__(self, theme_manager: ThemeManager) -> None:
        super().__init__(theme_manager)
        self._index: int = 0; self._score: int = 0
        self._answer: int = 0; self._problem: str = ""

    @property
    def name(self) -> str:        return "Math Challenge"
    @property
    def description(self) -> str: return "Solve math problems fast!"

    # ── CLI ────────────────────────────────────────────────────
    def play(self) -> None:
        self._say("🎮 Let's play MATH CHALLENGE!")
        score = 0
        for i in range(1, self.TOTAL + 1):
            problem, answer = self._generate_problem()
            print(f"\n{self._primary(f'Problem {i}/{self.TOTAL}: {problem} = ?')}")
            try:
                user_ans = int(input(Fore.GREEN + "Your answer: " + Style.RESET_ALL).strip())
                if user_ans == answer:
                    self._say("✅ Correct!"); score += 1
                else:
                    self._say(f"❌ Wrong! The answer was {answer}")
            except ValueError:
                self._say(f"❌ Invalid input! The answer was {answer}")
        print(f"\n{self._primary(f'🎯 Final Score: {score}/{self.TOTAL}')}")
        self._score_feedback(score, self.TOTAL)

    # ── GUI ────────────────────────────────────────────────────
    def start_game(self) -> dict:
        self._index = 0
        self._score = 0
        self._problem, self._answer = self._generate_problem()
        return {
            "message": (
                "\U0001f3ae Let's play MATH CHALLENGE!\n\n"
                f"Problem 1 of {self.TOTAL}:"
            ),
            "prompt": f"{self._problem}  =  ?",
            "done":   False,
        }

    def submit_answer(self, user_input: str) -> dict:
        try:
            user_ans = int(user_input.strip())
        except ValueError:
            feedback = f"❌ Invalid input! The answer was {self._answer}"
            self._index += 1
            return self._build_result(feedback)
        if user_ans == self._answer:
            self._score += 1; feedback = "✅ Correct!"
        else:
            feedback = f"❌ Wrong! The answer was {self._answer}"
        self._index += 1
        return self._build_result(feedback)

    def _build_result(self, feedback: str) -> dict:
        if self._index >= self.TOTAL:
            fb = self._score_feedback_text(self._score, self.TOTAL)
            return {"message": f"{feedback}\n\n🎯 Final Score: {self._score}/{self.TOTAL}\n{fb}", "prompt": "", "done": True, "score": f"{self._score}/{self.TOTAL}"}
        self._problem, self._answer = self._generate_problem()
        return {
            "message": f"{feedback}\n\nProblem {self._index + 1} of {self.TOTAL}:",
            "prompt":  f"{self._problem}  =  ?",
            "done":    False,
        }

    @staticmethod
    def _generate_problem() -> tuple[str, int]:
        op = random.choice(["+", "-", "*"])
        if op == "*":
            a, b = random.randint(2, 12), random.randint(2, 12); return f"{a} × {b}", a * b
        a, b = random.randint(1, 20), random.randint(1, 20)
        return (f"{a} + {b}", a + b) if op == "+" else (f"{a} - {b}", a - b)


# ══════════════════════════════════════════════════════════════
#  GameSession  —  active-game router for the GUI
# ══════════════════════════════════════════════════════════════
class GameSession:
    """
    Tracks one active game at a time and routes GUI answers to it.
    The CLI doesn't use this — it calls game.play() directly.

    Usage:
        session = GameSession()
        opening = session.start(game_object)   # → opening dict
        result  = session.answer("user text")  # → result dict
    """

    def __init__(self) -> None:
        self._active_game: BaseGame | None = None

    def start(self, game: BaseGame) -> dict:
        """Start *game* and return its opening state dict."""
        self._active_game = game
        return game.start_game()

    def answer(self, user_input: str) -> dict:
        """Route *user_input* to the active game's submit_answer()."""
        if not self._active_game:
            return {"message": "No game is currently active.", "prompt": "", "done": True}
        result = self._active_game.submit_answer(user_input)
        if result.get("done"):
            self._active_game = None
        return result

    def cancel(self) -> None:
        """Abort the current game without processing an answer."""
        self._active_game = None

    @property
    def is_active(self) -> bool:
        return self._active_game is not None

    @property
    def current_game_name(self) -> str:
        return self._active_game.name if self._active_game else ""


# ══════════════════════════════════════════════════════════════
#  GameManager  —  registry and dispatcher
# ══════════════════════════════════════════════════════════════
class GameManager:
    """
    Holds the list of registered games, builds menus, and
    dispatches the correct game when the user types !game.
    Adding a new game requires zero changes to existing code —
    just register() a new BaseGame subclass.
    """

    def __init__(self, theme_manager: ThemeManager) -> None:
        self._theme = theme_manager
        self._games: list[BaseGame] = []
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register(TriviaGame(self._theme))
        self.register(WordScramble(self._theme))
        self.register(MathChallenge(self._theme))
        self.register(GuessingGame(self._theme))

    def register(self, game: BaseGame) -> None:
        """Add *game* to the registry."""
        self._games.append(game)

    def get_games(self) -> list[BaseGame]:
        """Return a copy of the registered game list."""
        return list(self._games)

    # ── CLI display ────────────────────────────────────────────
    def show_menu(self) -> None:
        """Print the numbered game menu to stdout (CLI)."""
        print(f"\n{self._theme.color('primary')}🎮 GAME MENU 🎮")
        print(Fore.WHITE + "Choose a game:")
        for idx, game in enumerate(self._games, 1):
            print(f"{Fore.GREEN}  {idx}. {Fore.WHITE}{game.name} {Fore.YELLOW}— {game.description}")
        print(f"\n{Fore.CYAN}💡 Type: !game <number> or !game <n>\n")

    def get_menu_text(self) -> str:
        """Return the game menu as a plain string (GUI)."""
        lines = ["🎮 GAME MENU\n", "Choose a game:\n"]
        for idx, game in enumerate(self._games, 1):
            lines.append(f"  {idx}. {game.name} — {game.description}")
        lines.append("\nType: !game <number> or !game <n>")
        return "\n".join(lines)

    # ── CLI dispatch ───────────────────────────────────────────
    def dispatch(self, args: str) -> None:
        """Select and run a game by number or name keyword (CLI)."""
        args = args.strip().lower()
        if not args:
            self.show_menu(); return
        if args.isdigit():
            idx = int(args) - 1
            if 0 <= idx < len(self._games):
                self._games[idx].play(); return
            print(Fore.YELLOW + f"❓ No game #{args}. Type !game to see the menu.")
            return
        for game in self._games:
            if args in game.name.lower() or args in game.description.lower():
                game.play(); return
        print(Fore.YELLOW + f"❓ Game '{args}' not found. Type !game to see the menu.")

    # ── GUI lookup helpers ─────────────────────────────────────
    def get_game_by_index(self, idx: int) -> BaseGame | None:
        """Return the game at 0-based *idx*, or None if out of range."""
        return self._games[idx] if 0 <= idx < len(self._games) else None

    def get_game_by_name(self, name: str) -> BaseGame | None:
        """Return the first game whose name or description contains *name*."""
        name = name.strip().lower()
        for game in self._games:
            if name in game.name.lower() or name in game.description.lower():
                return game
        return None
