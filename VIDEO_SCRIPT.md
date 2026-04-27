# 🎬 Cosmo AI — Video Presentation Script

**Project:** Cosmo AI — CS50P Final Project
**Author:** Ali Saad
**Duration:** ~5 minutes
**Format:** Screen recording with voiceover

---

## 🎙️ PRODUCTION NOTES

- Record your screen at 1920×1080, window maximised
- Use a clean desktop background (no icons visible)
- Speak at a calm, clear pace — not too fast
- Pause 1–2 seconds between each major demo action
- The GUI should be open and visible for the entire video
- Run `python gui.py` before you start recording

---

## PART 1 — INTRODUCTION (0:00 – 0:40)

*[Show the Cosmo GUI window, fully open, welcome message visible]*

**SPEAK:**

"Hi, I'm Ali Saad, and this is Cosmo AI — my final project for CS50P.

Cosmo is an intelligent, personality-driven chatbot that you can
actually have a conversation with. It's not a simple keyword matcher
or a decision tree. It recognises 23 different types of intent,
remembers who you are across sessions, does maths, plays games, and
it can even learn new things that you teach it.

The whole project is built in Python using a full Object-Oriented
architecture — 13 classes, 6 modules, and 117 automated tests.

Let me show you how it works."

---

## PART 2 — FIRST IMPRESSION (0:40 – 1:10)

*[Delete user_data.json if it exists, close and reopen the app]*
*[The onboarding dialog appears]*

**SPEAK:**

"When you launch Cosmo for the first time, it asks for your name.
This is stored locally so Cosmo can remember you across every session."

*[Type your name — for example "Ali" — and press Enter]*

**SPEAK:**

"And there it is — Cosmo greets me personally. From now on, every
time I open the app, it goes straight to the chat. No dialog, just
a personalised welcome."

*[Briefly close and reopen the app to show returning user flow]*

---

## PART 3 — NATURAL CONVERSATION (1:10 – 2:00)

*[Type each message, pause briefly after each response]*

**SPEAK:**

"Let's start with a simple conversation. I'll just talk to it naturally."

*[Type:] `hello`*

"It greets me with a time-aware message — morning, afternoon, or
evening depending on when I'm actually talking to it."

*[Type:] `how are you`*

"Cosmo has a real personality. It's witty, slightly playful, and
never robotic."

*[Type:] `tell me a joke`*

"The responses are randomly selected from a pool of responses for
each intent, so you get variety in every conversation."

*[Type:] `who made you`*

"It even knows its own origin story."

*[Type:] `what time is it`*

"Live data — it reads from your system clock."

*[Type:] `i'm feeling sad today`*

"And when you're not doing well, Cosmo responds with genuine empathy."

---

## PART 4 — CALCULATOR (2:00 – 2:25)

*[Type each command and pause to show the result]*

**SPEAK:**

"Cosmo has a built-in calculator — and it's not just basic maths."

*[Type:] `!calc sqrt(144)`*

*[Type:] `!calc 2 ** 10`*

*[Type:] `!calc pi * 2`*

"Trigonometry, logarithms, powers, constants — all in a completely
safe sandboxed environment. You can't use it to run system commands
or access files — only pure maths."

*[Type:] `!calc 5 / 0`*

"And when something goes wrong, it tells you clearly instead of
crashing."

---

## PART 5 — MINI-GAMES (2:25 – 3:30)

*[Type:] `!game`*

**SPEAK:**

"Cosmo has four built-in mini-games. Let me show you two of them."

*[The game picker appears — click on Trivia Quiz]*

**SPEAK:**

"First, the Trivia Quiz. Five multiple-choice technology questions."

*[Answer a couple of questions — one correct, one wrong deliberately]*

"Correct answers give you a green tick. Wrong answers show you what
the right answer was. At the end, you get your final score and a
performance rating."

*[Finish the trivia game, click Return to Chat]*

**SPEAK:**

"Notice how the game replaced the chat area completely, then slid
back when I clicked Return. The chat history is still exactly where
it was."

*[Type:] `!game 4`*

**SPEAK:**

"Now the number guessing game. Cosmo picks a secret number between
1 and 10 and gives me hints after each wrong guess."

*[Guess a few numbers, including one too high and one too low]*

"Too high. Too low. Let me narrow it down."

*[Guess the correct number]*

"Got it. Every game tracks your score and tells you how well you did."

---

## PART 6 — LEARNING SYSTEM (3:30 – 4:00)

*[Type something Cosmo doesn't know — e.g. "xyzunknown1"]*

**SPEAK:**

"Now here's one of my favourite features. What happens when Cosmo
doesn't understand something?"

*[It returns an unknown response]*

*[Type another unknown message — e.g. "xyzunknown2"]*

**SPEAK:**

"The second time it doesn't understand, Cosmo offers to learn.
Watch this."

*[The teach prompt appears]*

*[Type:] `That's a secret phrase!`*

"Now Cosmo has learned it."

*[Type:] `xyzunknown2`*

"And it remembers. Even if I close the app and come back tomorrow,
it will still know that response — because it's saved to a JSON file."

---

## PART 7 — COMMANDS & HISTORY (4:00 – 4:25)

*[Type:] `!help`*

**SPEAK:**

"Every feature in Cosmo is accessible through a `!` command system.
!help shows the full list."

*[Type:] `!stats`*

"!stats shows me how many messages we've exchanged in total."

*[Type:] `!history 5`*

"!history shows me the last few exchanges — all with timestamps.
Everything is logged to a text file automatically."

*[Type:] `!theme magenta`*

"And !theme switches the colour scheme. There are five themes to
choose from, and your preference is saved automatically."

---

## PART 8 — CLOSING (4:25 – 5:00)

*[Type:] `bye`*

*[Cosmo says goodbye, input locks]*

**SPEAK:**

"When you're done, just say goodbye. Cosmo replies, and the session
ends cleanly.

To summarise what you just saw — Cosmo has:
- 23 conversation intents with natural language recognition
- A safe calculator with 14 mathematical functions
- Four playable mini-games with a full GUI state-machine
- A learning system that persists new knowledge to disk
- A complete command interface
- A personalised user memory system
- And a modern ChatGPT-style dark-mode interface — all built with
  Tkinter and pure Python

The architecture is fully Object-Oriented: 13 classes across 6
modules, with every OOP principle applied — encapsulation,
abstraction, inheritance, polymorphism, composition, single
responsibility, and dependency injection.

I'm Ali Saad, and this was Cosmo AI for CS50P. Thank you."

*[End recording]*

---

## 📋 DEMO CHECKLIST

Run through this before recording to make sure everything is ready:

- [ ] `user_data.json` deleted — so the onboarding dialog appears
- [ ] `responses.json` does NOT have `"xyzunknown2"` in learned —
  delete it if it does so the teach demo works
- [ ] `python gui.py` runs without errors
- [ ] All 117 tests pass: `pytest test_project.py -q`
- [ ] Screen resolution is 1920×1080
- [ ] Window is maximised
- [ ] No notifications will interrupt (enable Do Not Disturb)
- [ ] Microphone tested — no background noise
- [ ] You have practised the script at least once

---

## 🎯 TIMING GUIDE

| Part | Topic | Duration |
|---|---|---|
| 1 | Introduction | 0:40 |
| 2 | First impression / onboarding | 0:30 |
| 3 | Natural conversation | 0:50 |
| 4 | Calculator | 0:25 |
| 5 | Mini-games (Trivia + Guessing) | 1:05 |
| 6 | Learning system | 0:30 |
| 7 | Commands and history | 0:25 |
| 8 | Closing | 0:35 |
| **Total** | | **~5:00** |

---

## 💡 TIPS FOR A GREAT RECORDING

**Typing speed:** Type at a natural, readable pace. Not too fast —
viewers need to see what you're typing. Not too slow — keep the energy up.

**Pausing:** After each response from Cosmo, pause 1–2 seconds before
typing the next message. This gives viewers time to read the response.

**Mouse:** Keep your mouse movements calm and deliberate. Avoid rapid
cursor movement between thoughts.

**Mistakes:** If you type something wrong, it's fine to backspace
and retype. Don't stop the recording for small typos. If something
goes seriously wrong, just restart the recording from that section.

**Voice:** Speak clearly and with genuine enthusiasm. You built this —
let that come through. You don't need to be robotic; a natural
conversational tone works best.

**Resolution:** If the text in the recording looks blurry, increase
the zoom level in the app or increase your screen font size before
recording.

---

*Script written for Cosmo v3.1 — CS50P Final Project Presentation*
*Ali Saad*
