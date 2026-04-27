"""
test_project.py — Cosmo v3.1 (5-File Layout)
=============================================
117 unit tests covering every class.
All imports use the flat 5-file module layout.

Run with:
    pytest test_project.py -v
"""

import json
import pytest
from unittest.mock import MagicMock

# ── Imports from the five source files ────────────────────────
from theme  import ThemeManager
from memory import Logger, MessageHistory, UserProfile
from brain  import Calculator, ResponseEngine, CommandHandler, TEACH_PROMPT
from games  import (
    BaseGame, GuessingGame, TriviaGame, WordScramble,
    MathChallenge, GameSession, GameManager,
)
from bot    import CosmoBot


# ══════════════════════════════════════════════════════════════
#  ThemeManager
# ══════════════════════════════════════════════════════════════
class TestThemeManager:

    def test_default_theme_is_cyan(self):
        assert ThemeManager().current_name == "cyan"

    def test_apply_valid_theme(self):
        tm  = ThemeManager()
        msg = tm.apply("green")
        assert "Matrix Green" in msg and tm.current_name == "green"

    def test_apply_invalid_theme_returns_error(self):
        assert "not found" in ThemeManager().apply("rainbow").lower()

    def test_load_from_file(self, tmp_path):
        f = tmp_path / "u.json"
        f.write_text(json.dumps({"theme": "magenta"}))
        tm = ThemeManager(data_file=str(f)); tm.load()
        assert tm.current_name == "magenta"

    def test_save_to_file(self, tmp_path):
        f = tmp_path / "u.json"
        ThemeManager(data_file=str(f)).save("yellow")
        assert json.loads(f.read_text())["theme"] == "yellow"

    def test_hex_color_returns_hash_string(self):
        val = ThemeManager().hex_color("primary")
        assert val.startswith("#") and len(val) == 7

    def test_all_names_has_five_entries(self):
        assert len(ThemeManager().all_names) == 5

    def test_list_themes_plain_has_no_ansi(self):
        listing = ThemeManager().list_themes_plain()
        assert "\x1b" not in listing and "cyan" in listing


# ══════════════════════════════════════════════════════════════
#  Logger
# ══════════════════════════════════════════════════════════════
class TestLogger:

    def test_log_creates_file(self, tmp_path):
        Logger(str(tmp_path / "chat.txt")).log("Ali", "Hello!")
        assert (tmp_path / "chat.txt").exists()

    def test_log_writes_content(self, tmp_path):
        log = Logger(str(tmp_path / "chat.txt"))
        log.log("Ali", "Test message")
        text = (tmp_path / "chat.txt").read_text()
        assert "Ali" in text and "Test message" in text

    def test_read_returns_list(self, tmp_path):
        log = Logger(str(tmp_path / "chat.txt"))
        log.log("Ali", "Hi"); log.log("Cosmo", "Hey!")
        assert isinstance(log.read(10), list)

    def test_read_respects_limit(self, tmp_path):
        log = Logger(str(tmp_path / "chat.txt"))
        for i in range(20):
            log.log("Ali", f"msg{i}"); log.log("Cosmo", f"reply{i}")
        assert len(log.read(3)) <= 6

    def test_stats_on_missing_file(self, tmp_path):
        assert Logger(str(tmp_path / "nope.txt")).stats() == {"total": 0, "user": 0, "bot": 0}

    def test_stats_counts_correctly(self, tmp_path):
        log = Logger(str(tmp_path / "chat.txt"))
        log.log("Ali", "Hi"); log.log("Cosmo", "Hey!")
        log.log("Ali", "Bye"); log.log("Cosmo", "Cya!")
        s = log.stats()
        assert s["total"] == 4 and s["user"] == 2 and s["bot"] == 2


# ══════════════════════════════════════════════════════════════
#  MessageHistory
# ══════════════════════════════════════════════════════════════
class TestMessageHistory:

    def test_empty_on_creation(self):      assert len(MessageHistory()) == 0
    def test_add_and_retrieve(self):
        mh = MessageHistory(); mh.add("Ali", "Hello")
        msgs = mh.get_all()
        assert len(msgs) == 1 and msgs[0]["sender"] == "Ali" and msgs[0]["text"] == "Hello"

    def test_clear_empties_buffer(self):
        mh = MessageHistory(); mh.add("Ali", "Hello"); mh.clear()
        assert len(mh) == 0

    def test_get_all_returns_copy(self):
        mh = MessageHistory(); mh.add("Ali", "Hello")
        copy = mh.get_all(); copy.clear()
        assert len(mh) == 1   # original unaffected


# ══════════════════════════════════════════════════════════════
#  UserProfile
# ══════════════════════════════════════════════════════════════
class TestUserProfile:

    def test_load_missing_returns_empty(self, tmp_path):
        assert UserProfile(str(tmp_path / "missing.json")).load() == {}

    def test_save_and_load_roundtrip(self, tmp_path):
        f = tmp_path / "u.json"
        p = UserProfile(str(f)); p._data = {"name": "Ali"}; p.save()
        assert UserProfile(str(f)).load()["name"] == "Ali"

    def test_reset_removes_file(self, tmp_path):
        f = tmp_path / "u.json"; f.write_text(json.dumps({"name": "Ali"}))
        p = UserProfile(str(f)); p.reset()
        assert not f.exists()

    def test_is_new_user_true(self, tmp_path):
        assert UserProfile(str(tmp_path / "u.json")).is_new_user() is True

    def test_is_new_user_false(self, tmp_path):
        f = tmp_path / "u.json"; f.write_text(json.dumps({"name": "Ali"}))
        assert UserProfile(str(f)).is_new_user() is False

    def test_register_strips_prefix(self, tmp_path):
        assert UserProfile(str(tmp_path / "u.json")).register("my name is ali") == "Ali"

    def test_register_capitalises(self, tmp_path):
        assert UserProfile(str(tmp_path / "u.json")).register("sara") == "Sara"

    def test_register_fallback_on_empty(self, tmp_path):
        assert UserProfile(str(tmp_path / "u.json")).register("") == "Friend"

    def test_name_property_default(self):
        assert UserProfile().name == "Friend"


# ══════════════════════════════════════════════════════════════
#  Calculator
# ══════════════════════════════════════════════════════════════
class TestCalculator:

    def setup_method(self): self.c = Calculator()

    def test_addition(self):           assert "4"    in self.c.evaluate("2 + 2")
    def test_multiplication(self):     assert "10"   in self.c.evaluate("5 * 2")
    def test_division(self):           assert "2.5"  in self.c.evaluate("5 / 2")
    def test_power(self):              assert "8"    in self.c.evaluate("2 ** 3")
    def test_sqrt(self):               assert "4"    in self.c.evaluate("sqrt(16)")
    def test_pi(self):                 assert "3.14" in self.c.evaluate("pi")
    def test_ceil(self):               assert "4"    in self.c.evaluate("ceil(3.2)")
    def test_floor(self):              assert "3"    in self.c.evaluate("floor(3.9)")
    def test_division_by_zero(self):   assert "zero"    in self.c.evaluate("5/0").lower()
    def test_empty_expression(self):   assert "provide" in self.c.evaluate("").lower()
    def test_invalid_syntax(self):     assert "error"   in self.c.evaluate("2 +* 3").lower()
    def test_unknown_function(self):   assert "error"   in self.c.evaluate("hack(5)").lower()
    def test_float_noise_cleaned(self):
        assert "4" in self.c.evaluate("sqrt(16)") and "4.0" not in self.c.evaluate("sqrt(16)")


# ══════════════════════════════════════════════════════════════
#  ResponseEngine
# ══════════════════════════════════════════════════════════════
class TestResponseEngine:

    def _make(self, tmp_path, extra=None):
        data = {"greeting": ["Hey!"], "farewell": ["Bye!"], "time": ["It's {time}."],
                "date": ["It's {weekday}, {date}."], "unknown": ["No idea."], "learned": {}}
        if extra: data.update(extra)
        f = tmp_path / "r.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        e = ResponseEngine(str(f)); e.load(); return e

    def test_load_success(self, tmp_path):        assert self._make(tmp_path).responses != {}
    def test_load_missing_returns_false(self, tmp_path):
        assert ResponseEngine(str(tmp_path / "missing.json")).load() is False

    def test_greeting_has_time_part(self, tmp_path):
        r = self._make(tmp_path).get_response("hello")
        assert any(w in r for w in ["morning", "afternoon", "evening", "Hey!"])

    def test_farewell(self, tmp_path):
        assert self._make(tmp_path).get_response("bye") == "Bye!"

    def test_unknown_response(self, tmp_path):
        assert self._make(tmp_path).get_response("xyzjibberish") == "No idea."

    def test_learned_takes_priority(self, tmp_path):
        e = self._make(tmp_path, extra={"learned": {"cosmo rocks": ["Yes!"]}})
        assert e.get_response("cosmo rocks") == "Yes!"

    def test_time_placeholder_replaced(self, tmp_path):
        assert "{time}" not in self._make(tmp_path).get_response("what time is it")

    def test_date_placeholder_replaced(self, tmp_path):
        r = self._make(tmp_path).get_response("what is today's date")
        assert "{date}" not in r and "{weekday}" not in r

    def test_second_unknown_returns_teach_prompt(self, tmp_path):
        e = self._make(tmp_path)
        e.get_response("unknownabc1")
        assert e.get_response("unknownabc2") == TEACH_PROMPT

    def test_confirm_teach_saves(self, tmp_path):
        e = self._make(tmp_path)
        e._pending_teach_input = "what is life"
        e.confirm_teach(True, "42")
        assert "what is life" in e.responses["learned"]

    def test_confirm_teach_declined(self, tmp_path):
        e = self._make(tmp_path)
        e._pending_teach_input = "something"
        assert e.confirm_teach(False) == "No idea."


# ══════════════════════════════════════════════════════════════
#  GuessingGame
# ══════════════════════════════════════════════════════════════
class TestGuessingGame:

    def setup_method(self): self.game = GuessingGame(ThemeManager())

    def test_name_and_desc_not_empty(self):
        assert self.game.name and self.game.description

    def test_start_game_not_done(self):
        assert self.game.start_game()["done"] is False

    def test_correct_guess_ends_game(self):
        self.game.start_game(); secret = self.game._secret
        r = self.game.submit_answer(str(secret))
        assert r["done"] is True and "got it" in r["message"].lower()

    def test_low_guess_hint(self):
        self.game.start_game(); self.game._secret = 9
        assert "low" in self.game.submit_answer("1")["message"].lower()

    def test_high_guess_hint(self):
        self.game.start_game(); self.game._secret = 1
        assert "high" in self.game.submit_answer("9")["message"].lower()

    def test_quit_ends_game(self):
        self.game.start_game()
        assert self.game.submit_answer("quit")["done"] is True

    def test_invalid_input(self):
        self.game.start_game()
        r = self.game.submit_answer("abc")
        assert r["done"] is False and "valid" in r["message"].lower()

    def test_out_of_range(self):
        self.game.start_game()
        assert self.game.submit_answer("99")["done"] is False


# ══════════════════════════════════════════════════════════════
#  TriviaGame
# ══════════════════════════════════════════════════════════════
class TestTriviaGame:

    def setup_method(self): self.game = TriviaGame(ThemeManager())

    def test_name(self):              assert self.game.name == "Trivia Quiz"
    def test_start_shows_question_1(self):
        r = self.game.start_game()
        assert r["done"] is False and "Question 1" in r["message"]

    def test_correct_answer(self):
        self.game.start_game()
        assert "correct" in self.game.submit_answer(TriviaGame.QUESTIONS[0]["answer"])["message"].lower()

    def test_wrong_answer(self):
        self.game.start_game()
        assert "wrong" in self.game.submit_answer("Z")["message"].lower()

    def test_full_game_done(self):
        self.game.start_game()
        for q in TriviaGame.QUESTIONS[:-1]: self.game.submit_answer(q["answer"])
        last = self.game.submit_answer(TriviaGame.QUESTIONS[-1]["answer"])
        assert last["done"] is True and "score" in last


# ══════════════════════════════════════════════════════════════
#  WordScramble
# ══════════════════════════════════════════════════════════════
class TestWordScramble:

    def setup_method(self): self.game = WordScramble(ThemeManager())

    def test_name(self):              assert self.game.name == "Word Scramble"
    def test_scramble_preserves_letters(self):
        assert sorted(WordScramble._scramble("python")) == sorted("python")
    def test_scramble_variety(self):
        assert len({WordScramble._scramble("algorithm") for _ in range(50)}) > 1

    def test_start_not_done(self):    assert self.game.start_game()["done"] is False
    def test_correct_answer(self):
        self.game.start_game()
        assert "correct" in self.game.submit_answer(WordScramble.WORDS[0]["word"])["message"].lower()

    def test_wrong_answer(self):
        self.game.start_game()
        assert "wrong" in self.game.submit_answer("zzzzz")["message"].lower()

    def test_full_game_done(self):
        self.game.start_game()
        for item in WordScramble.WORDS[:-1]: self.game.submit_answer(item["word"])
        assert self.game.submit_answer(WordScramble.WORDS[-1]["word"])["done"] is True


# ══════════════════════════════════════════════════════════════
#  MathChallenge
# ══════════════════════════════════════════════════════════════
class TestMathChallenge:

    def setup_method(self): self.game = MathChallenge(ThemeManager())

    def test_name(self):              assert self.game.name == "Math Challenge"
    def test_generate_problem_types(self):
        p, a = MathChallenge._generate_problem()
        assert isinstance(p, str) and isinstance(a, int)

    def test_start_has_problem_1(self):
        result = self.game.start_game()
        # "Problem 1" now lives in "message"; "prompt" holds the expression
        assert "Problem 1" in result["message"] or "=" in result["prompt"]

    def test_correct_answer(self):
        self.game.start_game()
        assert "correct" in self.game.submit_answer(str(self.game._answer))["message"].lower()

    def test_wrong_answer(self):
        self.game.start_game()
        assert "wrong" in self.game.submit_answer(str(self.game._answer + 999))["message"].lower()

    def test_invalid_input(self):
        self.game.start_game()
        assert "invalid" in self.game.submit_answer("abc")["message"].lower()

    def test_full_game_done(self):
        self.game.start_game()
        for _ in range(MathChallenge.TOTAL - 1): self.game.submit_answer(str(self.game._answer))
        assert self.game.submit_answer(str(self.game._answer))["done"] is True


# ══════════════════════════════════════════════════════════════
#  GameSession
# ══════════════════════════════════════════════════════════════
class TestGameSession:

    def test_not_active_initially(self):   assert GameSession().is_active is False
    def test_start_makes_active(self):
        s = GameSession(); s.start(GuessingGame(ThemeManager()))
        assert s.is_active is True

    def test_win_deactivates(self):
        s = GameSession(); g = GuessingGame(ThemeManager()); s.start(g)
        g._secret = 5; s.answer("5")
        assert s.is_active is False

    def test_cancel_deactivates(self):
        s = GameSession(); s.start(GuessingGame(ThemeManager())); s.cancel()
        assert s.is_active is False

    def test_answer_without_active_game(self):
        assert GameSession().answer("5")["done"] is True

    def test_current_game_name(self):
        s = GameSession(); s.start(TriviaGame(ThemeManager()))
        assert s.current_game_name == "Trivia Quiz"

    def test_name_empty_when_inactive(self):
        assert GameSession().current_game_name == ""


# ══════════════════════════════════════════════════════════════
#  GameManager
# ══════════════════════════════════════════════════════════════
class TestGameManager:

    def test_four_default_games(self):
        assert len(GameManager(ThemeManager()).get_games()) == 4

    def test_register_adds_game(self):
        gm = GameManager(ThemeManager()); mock = MagicMock(spec=GuessingGame)
        gm.register(mock); assert mock in gm.get_games()

    def test_get_by_valid_index(self):
        assert GameManager(ThemeManager()).get_game_by_index(0) is not None

    def test_get_by_invalid_index(self):
        assert GameManager(ThemeManager()).get_game_by_index(99) is None

    def test_get_by_name(self):
        assert GameManager(ThemeManager()).get_game_by_name("trivia") is not None

    def test_get_by_unknown_name(self):
        assert GameManager(ThemeManager()).get_game_by_name("fakegame") is None

    def test_menu_text_contains_all_games(self):
        text = GameManager(ThemeManager()).get_menu_text()
        assert "GAME MENU" in text
        for name in ("Trivia", "Scramble", "Math", "Guess"):
            assert name in text


# ══════════════════════════════════════════════════════════════
#  CommandHandler
# ══════════════════════════════════════════════════════════════
class TestCommandHandler:

    def _make(self, tmp_path):
        tm  = ThemeManager(); calc = Calculator(); games = GameManager(tm)
        log = Logger(str(tmp_path / "log.txt")); prof = UserProfile(str(tmp_path / "u.json"))
        eng = ResponseEngine()
        return CommandHandler(tm, calc, games, log, prof, eng)

    def test_parse_bang(self):
        assert CommandHandler.parse("!help") == (True, "help", "")
    def test_parse_slash(self):
        is_cmd, cmd, _ = CommandHandler.parse("/theme cyan")
        assert is_cmd and cmd == "theme"
    def test_parse_with_args(self):
        _, cmd, args = CommandHandler.parse("!calc 2 + 2")
        assert cmd == "calc" and args == "2 + 2"
    def test_parse_plain_text(self):
        assert CommandHandler.parse("hello") == (False, "", "")
    def test_parse_empty(self):
        assert CommandHandler.parse("") == (False, "", "")

    def test_help_returns_string(self, tmp_path):
        ok, msg = self._make(tmp_path).execute("help", "")
        assert ok and isinstance(msg, str) and len(msg) > 0

    def test_calc_returns_result(self, tmp_path):
        ok, msg = self._make(tmp_path).execute("calc", "2 + 2")
        assert ok and "4" in msg

    def test_stats_returns_string(self, tmp_path):
        ok, msg = self._make(tmp_path).execute("stats", "")
        assert ok and isinstance(msg, str)

    def test_history_returns_string(self, tmp_path):
        ok, msg = self._make(tmp_path).execute("history", "")
        assert ok and isinstance(msg, str)

    def test_unknown_command(self, tmp_path):
        ok, msg = self._make(tmp_path).execute("fakecommand", "")
        assert ok and "unknown" in msg.lower()

    def test_execute_never_returns_none(self, tmp_path):
        h = self._make(tmp_path)
        for cmd in ("help", "stats", "history", "calc"):
            _, msg = h.execute(cmd, "")
            assert msg is not None

    def test_help_text_no_ansi(self, tmp_path):
        assert "\x1b" not in self._make(tmp_path).get_help_text()

    def test_theme_list_plain(self, tmp_path):
        ok, msg = self._make(tmp_path).execute("theme", "list")
        assert ok and "\x1b" not in msg and "cyan" in msg

    def test_theme_apply_valid(self, tmp_path):
        ok, msg = self._make(tmp_path).execute("theme", "green")
        assert ok and "Matrix Green" in msg

    def test_theme_apply_invalid(self, tmp_path):
        ok, msg = self._make(tmp_path).execute("theme", "rainbow")
        assert ok and "not found" in msg.lower()


# ══════════════════════════════════════════════════════════════
#  CosmoBot
# ══════════════════════════════════════════════════════════════
class TestCosmoBot:

    def _make_bot(self, tmp_path):
        resp = {"greeting": ["Hey!"], "farewell": ["Bye!"], "unknown": ["No idea."], "learned": {}}
        rf = tmp_path / "responses.json"
        rf.write_text(json.dumps(resp), encoding="utf-8")
        bot = CosmoBot(
            responses_file=str(rf),
            user_data_file=str(tmp_path / "u.json"),
            log_file=str(tmp_path / "chat.txt"),
        )
        bot.boot(); bot._user_name = "Ali"
        return bot

    def test_boot_loads_responses(self, tmp_path):
        assert self._make_bot(tmp_path)._engine.responses != {}

    def test_process_normal_message(self, tmp_path):
        r, ended = self._make_bot(tmp_path).process_message("hello")
        assert not ended and isinstance(r, str)

    def test_process_exit_word(self, tmp_path):
        r, ended = self._make_bot(tmp_path).process_message("bye")
        assert ended is True and r == "Bye!"

    def test_process_empty_input(self, tmp_path):
        r, ended = self._make_bot(tmp_path).process_message("   ")
        assert r == "" and not ended

    def test_process_command(self, tmp_path):
        r, ended = self._make_bot(tmp_path).process_message("!calc 3 + 3")
        assert "6" in r and not ended

    def test_process_logs_user_input(self, tmp_path):
        bot = self._make_bot(tmp_path); bot.process_message("hello")
        assert "Ali" in (tmp_path / "chat.txt").read_text()

    def test_process_adds_to_history(self, tmp_path):
        bot = self._make_bot(tmp_path); bot.process_message("hello")
        assert len(bot.history) >= 1

    def test_initialize_user_capitalises(self, tmp_path):
        assert self._make_bot(tmp_path).initialize_user("sara") == "Sara"

    def test_teach_confirm(self, tmp_path):
        bot = self._make_bot(tmp_path)
        bot._engine._pending_teach_input = "what is cosmo"
        msg = bot.teach_confirm(True, "A cool chatbot!")
        assert "remember" in msg.lower() or "got it" in msg.lower()

    def test_all_properties_accessible(self, tmp_path):
        bot = self._make_bot(tmp_path)
        assert bot.theme   is not None
        assert bot.profile is not None
        assert bot.history is not None   # MessageHistory is empty but not None
        assert bot.games   is not None
        assert bot.session is not None
