import json
import random
import datetime
import os
import time
from colorama import Fore, Style, init

# Display Banner
def display_banner():
    """
===============================================================
Display & UI Functions
These handle visual output such as the ASCII banner and colors.
They set the chatbot's visual identity and prepare the interface.
===============================================================
    """

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
    ║                      Version 2.0                          ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(get_theme_color("primary") + Style.BRIGHT + banner)
    print(Fore.YELLOW + "    💡 Type '!help' to see all available commands")
    print(Fore.YELLOW + "    🎨 Type '!theme' to change colors")
    print(Fore.YELLOW + "    🎮 Type '!game' to play mini-games\n")


# Color themes configuration
THEMES = {
    "cyan": {
        "primary": Fore.CYAN,
        "secondary": Fore.LIGHTCYAN_EX,
        "accent": Fore.BLUE,
        "name": "Ocean Blue"
    },
    "green": {
        "primary": Fore.GREEN,
        "secondary": Fore.LIGHTGREEN_EX,
        "accent": Fore.LIGHTGREEN_EX,
        "name": "Matrix Green"
    },
    "magenta": {
        "primary": Fore.MAGENTA,
        "secondary": Fore.LIGHTMAGENTA_EX,
        "accent": Fore.MAGENTA,
        "name": "Purple Dream"
    },
    "yellow": {
        "primary": Fore.YELLOW,
        "secondary": Fore.LIGHTYELLOW_EX,
        "accent": Fore.YELLOW,
        "name": "Sunshine Yellow"
    },
    "red": {
        "primary": Fore.RED,
        "secondary": Fore.LIGHTRED_EX,
        "accent": Fore.RED,
        "name": "Ruby Red"
    }
}

# Global theme variable
current_theme = THEMES["cyan"]


# CALCULATOR
"""
===============================================================
Calculator Feature
Safely evaluates math expressions using a sandboxed environment,
allowing operations (+, -, *, /, sin, cos, sqrt, etc.)
===============================================================
"""

def handle_calculator_command(expression):
    if not expression:
        return "❓ Please provide an expression. Example: !calc 2 + 2"

    try:
        # Import math for advanced functions
        import math

        # Create safe namespace with only math functions
        safe_dict = {
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log,
            'log10': math.log10,
            'exp': math.exp,
            'pi': math.pi,
            'e': math.e,
            'abs': abs,
            'round': round,
            'pow': pow,
        }

        # Evaluate expression in safe environment
        result = eval(expression, {"__builtins__": {}}, safe_dict)

        return f"🧮 {expression} = {result}"

    except ZeroDivisionError:
        return "⚠️ Error: Cannot divide by zero!"
    except SyntaxError:
        return "⚠️ Error: Invalid mathematical expression."
    except NameError as e:
        return f"⚠️ Error: Unknown function or variable. Try: +, -, *, /, **, sqrt(), sin(), cos()"
    except Exception as e:
        return f"⚠️ Error calculating: {str(e)}"


"""
===============================================================
User Settings & Data Management
Handles saving/loading themes, remembering user names,
and logging conversations.
===============================================================
"""

def load_user_theme(filename="user_data.json"):
    """Load user's preferred theme from user data."""
    global current_theme

    if os.path.exists(filename):
        try:
            with open(filename, "r") as file:
                user_data = json.load(file)
                theme_name = user_data.get("theme", "cyan")
                current_theme = THEMES.get(theme_name, THEMES["cyan"])
        except:
            current_theme = THEMES["cyan"]
    else:
        current_theme = THEMES["cyan"]

def save_user_theme(theme_name, filename="user_data.json"):
    """Save user's theme preference."""
    user_data = {}

    if os.path.exists(filename):
        try:
            with open(filename, "r") as file:
                user_data = json.load(file)
        except:
            pass

    user_data["theme"] = theme_name

    with open(filename, "w") as file:
        json.dump(user_data, file, indent=2)

def handle_theme_command(args):
    """Handle theme change command."""
    global current_theme

    args = args.strip().lower()

    if args == "list" or args == "":
        message = "\n🎨 Available themes:\n"
        for key, theme in THEMES.items():
            marker = "→" if theme == current_theme else " "
            message += f"  {marker} {theme['primary']}{key}{Style.RESET_ALL} - {theme['name']}\n"
        message += f"\nUse: !theme <name> to switch themes"
        print(message)
        return None

    if args in THEMES:
        current_theme = THEMES[args]
        save_user_theme(args)
        print(current_theme["primary"] + f"✨ Theme changed to {THEMES[args]['name']}!")
        return None
    else:
        return f"❓ Theme '{args}' not found. Type !theme list to see available themes."

def get_theme_color(color_type="primary"):
    """Get current theme color."""
    return current_theme.get(color_type, Fore.CYAN)


# Initialize colorama
init(convert=True, autoreset=True)


"""
===============================================================
Core Chat Features
Handles loading responses, typing animation, remembering users,
and logging all conversations.
===============================================================
"""
def load_responses(filename="responses.json"):
    """Load chatbot responses from a JSON file."""
    try:
        with open(filename, "r") as file:
            responses = json.load(file)
        return responses
    except FileNotFoundError:
        print(Fore.RED + "⚠️ Error: responses.json file not found.")
        return {}

def typing_effect(text, delay=0.03, use_theme=True):
    """Simulate typing effect for Cosmo."""
    if use_theme:
        text = get_theme_color("primary") + text

    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)
    print(Style.RESET_ALL)

def remember_user(filename="user_data.json"):
    """Remembers the user's name across sessions."""
    user_data = {}

    if os.path.exists(filename):
        with open(filename, "r") as file:
            user_data = json.load(file)

    if "name" in user_data:
        print(Fore.CYAN + f"🤖 Cosmo: Welcome back, {user_data['name']}!")
        return user_data["name"]
    else:
        name_input = input(Fore.GREEN + "🤖 Cosmo: What’s your name? " + Style.RESET_ALL)
        # Clean up full-sentence names like "my name is ali"
        for prefix in ["my name is", "i am", "i'm"]:
            if name_input.lower().startswith(prefix):
                name_input = name_input[len(prefix):].strip()
                break

        name = name_input.strip().capitalize()
        user_data["name"] = name

        with open(filename, "w") as file:
            json.dump(user_data, file)

        print(Fore.CYAN + f"🤖 Cosmo: Nice to meet you, {name}!")
        return name

def log_conversation(user, message):
    """Log chat history to a file with timestamps."""
    with open("chat_log.txt", "a", encoding="utf-8") as log:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.write(f"[{timestamp}] {user}: {message}\n")


"""
===============================================================
Game System
Includes all mini-games Cosmo can run:
- Number Guessing Game
- Trivia Quiz
- Word Scramble
- Math Challenge
Also includes a unified !game command handler.
===============================================================
"""

def play_guessing_game():
    """Play a number guessing game (1-10)."""
    typing_effect("🎮 Cosmo: Let's play a number guessing game (1–10)!")
    secret = random.randint(1, 10)  # This should generate random number
    attempts = 0

    while True:
        try:
            guess_input = input(Fore.GREEN + "Your guess: " + Style.RESET_ALL).strip()

            # Allow player to quit
            if guess_input.lower() in ['quit', 'exit', 'stop']:
                typing_effect(f"🤖 Cosmo: The number was {secret}. Better luck next time!")
                return

            guess = int(guess_input)
            attempts += 1

            if guess < 1 or guess > 10:
                typing_effect("🤖 Cosmo: Please enter a number between 1 and 10!")
                continue

            if guess == secret:
                typing_effect(f"🎉 Cosmo: You got it in {attempts} attempt(s)! That was fun!")
                break
            elif guess < secret:
                typing_effect("🤖 Cosmo: Too low! Try again.")
            else:
                typing_effect("🤖 Cosmo: Too high! Try again.")

        except ValueError:
            typing_effect("🤖 Cosmo: Please enter a valid number between 1 and 10!")

def play_trivia_game():
    """Play a trivia quiz game."""
    typing_effect("🎮 Cosmo: Let's play TRIVIA! Answer these questions:")

    questions = [
        {
            "question": "What does CPU stand for?",
            "options": ["A) Central Processing Unit", "B) Computer Personal Unit", "C) Central Program Utility", "D) Core Processing Unit"],
            "answer": "A"
        },
        {
            "question": "Which programming language is known as the 'language of the web'?",
            "options": ["A) Python", "B) Java", "C) JavaScript", "D) C++"],
            "answer": "C"
        },
        {
            "question": "What year was Python first released?",
            "options": ["A) 1989", "B) 1991", "C) 1995", "D) 2000"],
            "answer": "B"
        },
        {
            "question": "What does HTML stand for?",
            "options": ["A) Hyperlinks and Text Markup Language", "B) HyperText Markup Language", "C) Home Tool Markup Language", "D) Hyperlinking Text Marking Language"],
            "answer": "B"
        },
        {
            "question": "Who is known as the father of computers?",
            "options": ["A) Bill Gates", "B) Steve Jobs", "C) Charles Babbage", "D) Alan Turing"],
            "answer": "C"
        }
    ]

    score = 0
    total = len(questions)

    for i, q in enumerate(questions, 1):
        print(f"\n{get_theme_color('primary')}Question {i}/{total}: {q['question']}")
        for option in q['options']:
            print(Fore.WHITE + f"  {option}")

        answer = input(Fore.GREEN + "Your answer (A/B/C/D): " + Style.RESET_ALL).strip().upper()

        if answer == q['answer']:
            typing_effect("✅ Correct! Great job!")
            score += 1
        else:
            typing_effect(f"❌ Wrong! The correct answer was {q['answer']}")

    print(f"\n{get_theme_color('primary')}🎯 Final Score: {score}/{total}")

    if score == total:
        typing_effect("🏆 Perfect score! You're a trivia master!")
    elif score >= total * 0.7:
        typing_effect("🌟 Great job! You really know your stuff!")
    elif score >= total * 0.5:
        typing_effect("👍 Not bad! Keep learning!")
    else:
        typing_effect("📚 Keep studying! You'll do better next time!")

def play_word_scramble():
    """Play a word scramble game."""
    typing_effect("🎮 Cosmo: Let's play WORD SCRAMBLE! Unscramble the words:")

    words = [
        {"word": "python", "hint": "A popular programming language (snake!)"},
        {"word": "computer", "hint": "Electronic device for processing data"},
        {"word": "keyboard", "hint": "Input device with keys"},
        {"word": "algorithm", "hint": "Step-by-step problem-solving procedure"},
        {"word": "database", "hint": "Organized collection of data"}
    ]

    score = 0
    total = len(words)

    for i, item in enumerate(words, 1):
        word = item["word"]
        scrambled = ''.join(random.sample(word, len(word)))

        # Make sure it's actually scrambled
        while scrambled == word and len(word) > 1:
            scrambled = ''.join(random.sample(word, len(word)))

        print(f"\n{get_theme_color('primary')}Round {i}/{total}")
        print(f"{Fore.YELLOW}Scrambled word: {scrambled.upper()}")
        print(f"{Fore.CYAN}Hint: {item['hint']}")

        guess = input(Fore.GREEN + "Your answer: " + Style.RESET_ALL).strip().lower()

        if guess == word:
            typing_effect("✅ Correct! Well done!")
            score += 1
        else:
            typing_effect(f"❌ Wrong! The answer was: {word}")

    print(f"\n{get_theme_color('primary')}🎯 Final Score: {score}/{total}")

    if score == total:
        typing_effect("🏆 Perfect! You're a word wizard!")
    elif score >= total * 0.6:
        typing_effect("🌟 Great job!")
    else:
        typing_effect("💪 Keep practicing!")

def play_math_challenge():
    """Play a math challenge game."""
    typing_effect("🎮 Cosmo: Let's play MATH CHALLENGE! Solve these problems:")

    score = 0
    total = 5

    for i in range(1, total + 1):
        # Generate random math problem
        num1 = random.randint(1, 20)
        num2 = random.randint(1, 20)
        operation = random.choice(['+', '-', '*'])

        if operation == '+':
            answer = num1 + num2
            problem = f"{num1} + {num2}"
        elif operation == '-':
            answer = num1 - num2
            problem = f"{num1} - {num2}"
        else:  # multiplication
            num1 = random.randint(2, 12)
            num2 = random.randint(2, 12)
            answer = num1 * num2
            problem = f"{num1} × {num2}"

        print(f"\n{get_theme_color('primary')}Problem {i}/{total}: {problem} = ?")

        try:
            user_answer = int(input(Fore.GREEN + "Your answer: " + Style.RESET_ALL).strip())

            if user_answer == answer:
                typing_effect("✅ Correct!")
                score += 1
            else:
                typing_effect(f"❌ Wrong! The answer was {answer}")
        except ValueError:
            typing_effect(f"❌ Invalid input! The answer was {answer}")

    print(f"\n{get_theme_color('primary')}🎯 Final Score: {score}/{total}")

    if score == total:
        typing_effect("🏆 Perfect! You're a math genius!")
    elif score >= 4:
        typing_effect("🌟 Excellent work!")
    elif score >= 3:
        typing_effect("👍 Good job!")
    else:
        typing_effect("📐 Keep practicing your math!")

# Game Command
def handle_game_command(args):
    """Handle game selection and execution."""
    args = args.strip().lower()

    # If no specific game mentioned, show menu
    if not args or args == "":
        print(f"\n{get_theme_color('primary')}🎮 GAME MENU 🎮")
        print(f"{Fore.WHITE}Choose a game to play:")
        print(f"{Fore.GREEN}  1. {Fore.WHITE}Trivia Quiz {Fore.YELLOW}- Test your knowledge!")
        print(f"{Fore.GREEN}  2. {Fore.WHITE}Word Scramble {Fore.YELLOW}- Unscramble the words!")
        print(f"{Fore.GREEN}  3. {Fore.WHITE}Math Challenge {Fore.YELLOW}- Solve math problems!")
        print(f"{Fore.GREEN}  4. {Fore.WHITE}Number Guessing {Fore.YELLOW}- Guess the secret number (1-10)!")
        print(f"{Fore.CYAN}\n💡 Type: !game <number> or !game <name>")
        print(f"{Fore.CYAN}Example: !game 1  or  !game trivia\n")
        return

    # Game selection
    if args in ['1', 'trivia', 'quiz']:
        play_trivia_game()
    elif args in ['2', 'scramble', 'word', 'word scramble']:
        play_word_scramble()
    elif args in ['3', 'math', 'challenge', 'math challenge']:
        play_math_challenge()
    elif args in ['4', 'guess', 'number', 'guessing', 'number guessing']:
        play_guessing_game()
    else:
        print(Fore.YELLOW + f"❓ Game '{args}' not found. Type !game to see available games.")


"""
===============================================================
User Responses Handling :
- Loading and saving bot responses
- Generating responses based on user input
- Handling unknown questions and teaching Cosmo new responses
===============================================================
"""

def save_responses(responses, filename="responses.json"):
    with open(filename, "w") as file:
        json.dump(responses, file, indent=2)

# Track how many unknown responses happened
unknown_counter = 0

def get_response(user_input, responses):
    """Return chatbot response based on detected intent."""
    global unknown_counter
    user_input_lower = user_input.lower().strip()  # ← Make sure this line exists

    # Check for calculation requests
    calc_triggers = ["calculate", "calc", "what is", "what's", "solve"]
    if any(trigger in user_input_lower for trigger in calc_triggers):
        for trigger in calc_triggers:
            if trigger in user_input_lower:
                expression = user_input_lower.split(trigger, 1)[1].strip()
                if expression:
                    return handle_calculator_command(expression)

    triggers = {
        "greeting": ["hi", "hello", "hey", "sup", "hiya", "howdy"],
        "farewell": ["bye", "goodbye", "see you", "later", "farewell"],
        "time": ["time", "clock"],
        "date": ["date", "day", "today"],
        "joke": ["joke", "funny", "laugh"],
        "feeling": ["how are you", "feeling", "mood"],
        "acknowledge": ["ok", "fine", "got it", "understand", "thanks", "thank you"],
        "weather": ["weather", "forecast", "temperature"],
        "motivation": ["motivate", "inspire", "motivation", "encourage"],
        "compliment": ["smart", "good", "nice", "cool", "awesome"],
        "developer": ["code", "bug", "developer", "program", "programming"],
        "fact": ["fact", "info", "information", "tell me something"],
        "location": ["where", "place", "live", "location"],
        "game": ["game", "play"],
        "name": ["name", "who are you", "what are you"],
        "help": ["help", "what can you do", "commands"]
    }

    # First try exact matching
    for category, keywords in triggers.items():
        if any(keyword in user_input_lower for keyword in keywords):

            if category == "greeting":
                hour = datetime.datetime.now().hour
                if hour < 12:
                    greeting_time = "Good morning"
                elif hour < 18:
                    greeting_time = "Good afternoon"
                else:
                    greeting_time = "Good evening"
                base = random.choice(responses.get("greeting", ["Hey!"]))
                return f"{greeting_time}! {base}"

            if category == "game":
                handle_game_command("")

            response = random.choice(responses.get(category, responses["unknown"]))

            if "{time}" in response:
                response = response.format(time=datetime.datetime.now().strftime("%H:%M"))
            elif "{date}" in response or "{weekday}" in response:
                today = datetime.date.today()
                response = response.format(
                    date=today.strftime("%B %d, %Y"),
                    weekday=today.strftime("%A")
                )

            return response

    # If no exact match, handle as unknown
    unknown_counter += 1
    if unknown_counter % 2 == 0:
        teach = input(
            Fore.YELLOW + "🤖 Cosmo: I don't know that one. Would you like to teach me? (yes/no): ").strip().lower()
        if teach.startswith("y"):
            new_reply = input(Fore.YELLOW + "What should I say next time? " + Style.RESET_ALL)
            if "learned" not in responses:
                responses["learned"] = {}
            responses["learned"][user_input_lower] = [new_reply]
            save_responses(responses)
            typing_effect("🤖 Cosmo: Got it! I'll remember that next time.")
            return new_reply

    return random.choice(responses.get("unknown", ["I didn't quite get that."]))


"""
===============================================================
Command Parsing & Execution :
- Parsing commands starting with ! or /
- Executing commands like !help, !calc, !game, !theme, !history
- Command-specific handling functions for each command
===============================================================
"""

def parse_command(user_input):
    """
    Parse user input for commands starting with ! or /
    Returns: (is_command: bool, command: str, args: list)
    """
    user_input = user_input.strip()

    if user_input.startswith('!') or user_input.startswith('/'):
        parts = user_input[1:].split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        return True, command, args

    return False, "", ""


def handle_help_command():
    """Display all available commands."""
    help_text = f"""
{Fore.CYAN}╔═══════════════════════════════════════════════════════════╗
║                    📖 AVAILABLE COMMANDS                  ║
╚═══════════════════════════════════════════════════════════╝

{Fore.GREEN}🎨 Customization:
  {Fore.WHITE}!theme <name>     {Fore.YELLOW}- Change color theme (cyan/green/magenta/yellow/red)
  {Fore.WHITE}!theme list       {Fore.YELLOW}- Show all available themes

{Fore.GREEN}🎮 Games & Fun:
  {Fore.WHITE}!game             {Fore.YELLOW}- Play a mini-game
  {Fore.WHITE}!game trivia      {Fore.YELLOW}- Play trivia quiz
  {Fore.WHITE}!game scramble    {Fore.YELLOW}- Play word scramble
  {Fore.WHITE}!game math        {Fore.YELLOW}- Play math challenge
  {Fore.WHITE}!game guess       {Fore.YELLOW}- Play number guessing (1-10)

{Fore.GREEN}🔧 Utilities:
  {Fore.WHITE}!calc <expression> {Fore.YELLOW}- Calculate math expressions
  {Fore.WHITE}!history          {Fore.YELLOW}- View recent chat history
  {Fore.WHITE}!clear            {Fore.YELLOW}- Clear the screen

{Fore.GREEN}📊 Information:
  {Fore.WHITE}!stats            {Fore.YELLOW}- Show chat statistics
  {Fore.WHITE}!help             {Fore.YELLOW}- Show this help menu

{Fore.GREEN}⚙️ System:
  {Fore.WHITE}!reset            {Fore.YELLOW}- Reset your user profile
  {Fore.WHITE}bye/quit/exit     {Fore.YELLOW}- End the chat session
"""
    print(help_text)


def handle_clear_command():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')
    display_banner()
    print(Fore.GREEN + "✨ Screen cleared!\n")


def handle_history_command(limit=10):
    """Display recent chat history."""
    if not os.path.exists("chat_log.txt"):
        print(Fore.YELLOW + "📭 No chat history found yet.")
        return

    try:
        with open("chat_log.txt", "r", encoding="utf-8") as log:
            lines = log.readlines()
            recent = lines[-limit*2:] if len(lines) > limit*2 else lines

        print(Fore.CYAN + f"\n📜 Last {len(recent)//2} messages:\n")
        for line in recent:
            print(Fore.WHITE + line.strip())
        print()
    except Exception as e:
        print(Fore.RED + f"⚠️ Error reading history: {e}")


def handle_stats_command():
    """Display chat statistics."""
    if not os.path.exists("chat_log.txt"):
        print(Fore.YELLOW + "📭 No chat data available yet.")
        return

    try:
        with open("chat_log.txt", "r", encoding="utf-8") as log:
            lines = log.readlines()

        user_messages = len([l for l in lines if not "Cosmo:" in l])
        bot_messages = len([l for l in lines if "Cosmo:" in l])
        total = len(lines)

        print(Fore.CYAN + "\n📊 Chat Statistics:")
        print(Fore.WHITE + f"   Total messages: {total}")
        print(Fore.WHITE + f"   Your messages: {user_messages}")
        print(Fore.WHITE + f"   Cosmo's replies: {bot_messages}\n")
    except Exception as e:
        print(Fore.RED + f"⚠️ Error calculating stats: {e}")


def handle_reset_command(filename="user_data.json"):
    """Reset user profile after confirmation."""
    confirm = input(
        Fore.YELLOW + "⚠️ Are you sure you want to reset your profile? (yes/no): ").strip().lower()

    if confirm in ['yes', 'y']:
        if os.path.exists(filename):
            os.remove(filename)
        print(Fore.GREEN + "✅ Profile reset! Restart the program to create a new profile.")
        return True
    else:
        print(Fore.CYAN + "❌ Reset cancelled.")
        return False

def execute_command(command, args, user_name, responses):
    """
    Execute a command and return whether to continue the chat.
    Returns: (continue_chat: bool, custom_message: str or None)
    """
    if command == "help":
        handle_help_command()
        return True, None

    elif command == "clear":
        handle_clear_command()
        return True, None

    elif command == "history":
        try:
            limit = int(args) if args.isdigit() else 10
            handle_history_command(limit)
        except:
            handle_history_command()
        return True, None

    elif command == "stats":
        handle_stats_command()
        return True, None

    elif command == "reset":
        should_exit = handle_reset_command()
        return not should_exit, None

    elif command == "theme":
        # We'll implement this in Feature 3
        return True, handle_theme_command(args)

    elif command == "calc":
        # We'll implement this in Feature 4
        result = handle_calculator_command(args)
        return True, result

    elif command == "game":
        # We'll implement this in Feature 6
        handle_game_command(args)
        return True, None

    else:
        return True, f"❓ Unknown command: !{command}. Type !help for available commands."


"""
===============================================================
Main Chatbot Function
Handles:
- Loading user preferences and responses
- Logging conversations
- Parsing commands and user input
- Providing responses and dynamic teaching
===============================================================
"""

def main():
    """Main chatbot loop."""
    load_user_theme()  # Load theme first
    display_banner()

    print(get_theme_color("primary") + "🤖 Cosmo: Hello! I'm Cosmo, your chat buddy with personality!")
    print(get_theme_color("primary") + "Type 'bye', 'quit', or 'exit' to end the chat.\n")

    responses = load_responses()
    if not responses:
        print(Fore.RED + "⚠️ Could not load responses. Exiting program.")
        return

    user_name = remember_user()
    print(get_theme_color("primary") + f"🤖 Cosmo: How can I help you today, {user_name}?")

    while True:
        user_input = input(Fore.GREEN + f"{user_name}: " + Style.RESET_ALL).strip()

        # Skip empty inputs
        if not user_input:
            continue

        log_conversation(user_name, user_input)

        # Check for exit commands
        if user_input.lower() in ["bye", "quit", "exit"]:
            farewell = random.choice(responses["farewell"])
            typing_effect(f"🤖 Cosmo: {farewell}")
            log_conversation("Cosmo", farewell)
            break

        # Check for commands
        is_command, command, args = parse_command(user_input)

        if is_command:
            continue_chat, custom_message = execute_command(command, args, user_name, responses)

            if custom_message:
                typing_effect(f"🤖 Cosmo: {custom_message}")
                log_conversation("Cosmo", custom_message)

            if not continue_chat:
                break

            continue

        response = get_response(user_input, responses)
        typing_effect(f"🤖 Cosmo: {response}")
        log_conversation("Cosmo", response)


if __name__ == "__main__":
    main()
