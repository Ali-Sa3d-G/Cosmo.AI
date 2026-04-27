# 🤖 Cosmo AI — Your Cosmic Chat Companion

```
╔═══════════════════════════════════════════════════════════╗
║        ██████╗ ██████╗ ███████╗███╗   ███╗ ██████╗        ║
║       ██╔════╝██╔═══██╗██╔════╝████╗ ████║██╔═══██╗       ║
║       ██║     ██║   ██║███████╗██╔████╔██║██║   ██║       ║
║       ██║     ██║   ██║╚════██║██║╚██╔╝██║██║   ██║       ║
║       ╚██████╗╚██████╔╝███████║██║ ╚═╝ ██║╚██████╔╝       ║
║        ╚═════╝ ╚═════╝ ╚══════╝╚═╝     ╚═╝ ╚═════╝        ║
║          🤖 Your AI Chat Buddy with Personality 🤖        ║
║               Version 3.1 — GUI-Ready OOP Edition          ║
╚═══════════════════════════════════════════════════════════╝
```

**CS50P Final Project — Ali Saad**

---

## 📝 Description

Cosmo is an intelligent, personality-driven AI chatbot with a modern
ChatGPT-style dark-mode GUI built entirely in Python. It is not a
simple decision tree — it recognises 23 different conversation intents,
remembers who you are across sessions, performs mathematics, plays four
mini-games, and can learn new responses that you teach it on the fly.

The project is a full Object-Oriented rewrite of a functional-style
original, demonstrating every core OOP principle: encapsulation,
abstraction, inheritance, polymorphism, composition, Single
Responsibility, and the Open/Closed Principle. The architecture spans
13 classes across 6 modules, with 117 passing automated unit tests.

---

## 🚀 How to Run

### Install dependencies (once)

```bash
pip install -r requirements.txt
```

### Launch the GUI

```bash
python gui.py
```

### Launch the CLI (terminal version)

```bash
python main.py
```

### Run the automated tests

```bash
pytest test_project.py -v
```

---

## ✨ Features

### 💬 Natural Conversation
Cosmo recognises 23 intent categories through keyword matching:
greetings, farewells, time, date, jokes, feelings, weather, motivation,
compliments, developer topics, facts, location, games, name, help, age,
creator, programming language, hobbies, emotional states (sad/happy/bored),
and insults — all with witty, personality-driven responses.

### 🧠 Memory
- Remembers your name across every session (saved to `user_data.json`)
- All conversations are timestamped and logged to `chat_log.txt`
- **Learning system:** teach Cosmo new responses via the teach prompt;
  they are saved to `responses.json` and recalled immediately

### 🧮 Calculator
Safe mathematical expression evaluator using a sandboxed `eval()` with
a whitelist of 14 functions: `sqrt`, `sin`, `cos`, `tan`, `log`,
`log10`, `exp`, `ceil`, `floor`, `abs`, `round`, `pow`, `pi`, `e`.

```
!calc sqrt(144) + pi
!calc 2 ** 10
!calc sin(0)
```

### 🎮 Four Mini-Games
| Game | How to launch |
|---|---|
| Trivia Quiz (5 tech questions) | `!game 1` or `!game trivia` |
| Word Scramble (unscramble 5 words) | `!game 2` or `!game scramble` |
| Math Challenge (5 arithmetic rounds) | `!game 3` or `!game math` |
| Number Guessing (1–10) | `!game 4` or `!game guess` |

Each game has both a CLI (blocking loop) and a GUI (state-machine)
API so neither interface blocks the other's event loop.

### 🎨 Five Colour Themes
Cyan (Ocean Blue), Green (Matrix Green), Magenta (Purple Dream),
Yellow (Sunshine Yellow), Red (Ruby Red). Switch with `!theme <name>`.
Preference persists across sessions. In the GUI, colours repaint
immediately after switching.

### ⚙️ Command System

| Command | Action |
|---|---|
| `!help` | Show all available commands |
| `!theme <n>` | Switch colour theme |
| `!theme list` | List all themes |
| `!calc <expr>` | Evaluate a math expression |
| `!game` | Open the game picker |
| `!game <n>` | Launch a game by number or name |
| `!history [n]` | Show last n chat exchanges |
| `!stats` | Show message count statistics |
| `!clear` | Clear the chat screen |
| `!reset` | Reset your saved profile |
| `bye` / `quit` / `exit` | End the session |

All commands work with either `!` or `/` prefix.

---

## 📁 File Structure

```
cosmo_v5/
├── gui.py           — Tkinter GUI (4 classes, ~1100 lines)
├── main.py          — CLI entry point
├── bot.py           — CosmoBot orchestrator
├── brain.py         — Calculator, ResponseEngine, CommandHandler
├── games.py         — BaseGame + 4 games + GameSession + GameManager
├── memory.py        — Logger, MessageHistory, UserProfile
├── theme.py         — ThemeManager (ANSI + hex colours)
├── test_project.py  — 117 pytest unit tests
├── responses.json   — All bot response text
├── requirements.txt — colorama, rapidfuzz
├── user_data.json   — Auto-generated: saved name + theme
├── chat_log.txt     — Auto-generated: full conversation log
├── DOCUMENTATION.md — Full technical reference
├── TESTING_GUIDE.md — Complete manual testing guide
└── VIDEO_SCRIPT.md  — Presentation video script
```

---

## 🏗️ Architecture

```
gui.py / main.py
      │
      ▼
   bot.py  (CosmoBot — orchestrator, wires everything)
      │
      ├── theme.py    → ThemeManager
      ├── memory.py   → Logger, MessageHistory, UserProfile
      ├── brain.py    → Calculator, ResponseEngine, CommandHandler
      └── games.py    → BaseGame, 4 games, GameSession, GameManager
```

The dependency arrow always points downward. No module imports from
a module above it. `bot.py` is the only file that imports from all
four domain modules.

---

## 🎓 OOP Principles

| Principle | Where applied |
|---|---|
| **Encapsulation** | All state is private (`_attr`); access via methods |
| **Abstraction** | `BaseGame` ABC enforces the game contract via `@abstractmethod` |
| **Inheritance** | 4 game classes inherit shared helpers from `BaseGame` |
| **Polymorphism** | `GameSession.answer()` calls `game.submit_answer()` regardless of game type |
| **Composition** | `CosmoBot` composes all sub-systems via constructor injection |
| **SRP** | Each class has exactly one reason to change |
| **OCP** | New games/themes/commands require zero changes to existing code |
| **Dependency Injection** | Every class receives dependencies through `__init__` |

---

## 📚 Libraries

| Library | Purpose |
|---|---|
| `colorama` | Cross-platform ANSI terminal colours (CLI) |
| `rapidfuzz` | Fast fuzzy string matching (available for future use) |
| `tkinter` | GUI framework (Python standard library) |

**Python 3.10+ required** (for `match/case` syntax in `CommandHandler`).

---

## 🧪 Testing

```bash
# Run all 117 tests
pytest test_project.py -v

# Run a specific class
pytest test_project.py::TestCalculator -v
pytest test_project.py::TestTriviaGame -v
```

See `TESTING_GUIDE.md` for the complete manual testing checklist
covering every feature, command, game, and edge case.

---

## 👨‍💻 Author

**Ali Saad** — CS50P Student, Harvard University

*Made with ❤️ and ☕ for CS50P*
