import json
import os
import pytest
from unittest import mock
from project import load_responses, get_response, remember_user


def test_load_responses():
    """Test loading responses.json successfully."""
    sample_data = {
        "greeting": ["Hello!"],
        "farewell": ["Goodbye!"],
        "unknown": ["I didn't get that."]
    }

    with open("responses.json", "w") as f:
        json.dump(sample_data, f)

    responses = load_responses("responses.json")
    assert isinstance(responses, dict)
    assert "greeting" in responses
    assert responses["farewell"] == ["Goodbye!"]

    os.remove("responses.json")


def test_load_responses_file_not_found():
    """Ensure load_responses returns empty dict when file is missing."""
    responses = load_responses("non_existent.json")
    assert responses == {}


def test_get_response_basic():
    """Test chatbot response selection by keyword."""
    import project
    project.unknown_counter = 0  # Reset global state before test

    responses = {
        "greeting": ["Hi there!"],
        "farewell": ["Goodbye!"],
        "unknown": ["I'm not sure what you mean."]
    }

    response = get_response("hello", responses)
    assert response in responses["greeting"] or "Good morning" in response or "Good afternoon" in response or "Good evening" in response

    response = get_response("bye", responses)
    assert response in responses["farewell"]

    # Test unknown input (first call won't trigger teaching prompt)
    response = get_response("xyzabc123", responses)
    assert response in responses["unknown"]


def test_remember_user(tmp_path):
    """Test that the chatbot remembers and loads user name correctly."""
    file_path = tmp_path / "user_data.json"

    # Test new user
    with mock.patch("builtins.input", return_value="Ali"):
        name = remember_user(filename=file_path)
        assert name == "Ali"
        assert file_path.exists()

    # Test returning user (no mock needed, should just read file)
    name = remember_user(filename=file_path)
    assert name == "Ali"


def test_parse_command():
    """Test command parsing."""
    from project import parse_command

    # Test valid command
    is_cmd, cmd, args = parse_command("!help")
    assert is_cmd == True
    assert cmd == "help"
    assert args == ""

    # Test command with arguments
    is_cmd, cmd, args = parse_command("!calc 2 + 2")
    assert is_cmd == True
    assert cmd == "calc"
    assert args == "2 + 2"

    # Test non-command
    is_cmd, cmd, args = parse_command("hello there")
    assert is_cmd == False

    # Test slash command
    is_cmd, cmd, args = parse_command("/theme cyan")
    assert is_cmd == True
    assert cmd == "theme"

    def test_calculator_basic():
    """Test basic calculator operations."""
    from project import handle_calculator_command

    # Basic operations
    assert "4" in handle_calculator_command("2 + 2")
    assert "10" in handle_calculator_command("5 * 2")
    assert "2.5" in handle_calculator_command("5 / 2")

    # Error handling
    result = handle_calculator_command("5 / 0")
    assert "zero" in result.lower()

    result = handle_calculator_command("")
    assert "provide" in result.lower()


def test_calculator_advanced():
    """Test advanced calculator functions."""
    from project import handle_calculator_command

    # Square root
    result = handle_calculator_command("sqrt(16)")
    assert "4" in result

    # Power
    result = handle_calculator_command("2 ** 3")
    assert "8" in result
