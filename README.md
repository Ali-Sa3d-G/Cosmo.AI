# 🤖 COSMO - Your AI Chat Buddy

**CS50P Final Project**

Cosmo is an intelligent, personality-driven chatbot that runs entirely in your terminal. With features like user memory, customizable themes, mini-games, a learning system, and a powerful command interface, Cosmo offers an engaging and fun conversational experience.


**Made with ❤️ and ☕ for CS50P**

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

## 👨‍💻 Author

**Ali Saad** - CS50P Student

This project was created as the final project for Harvard's CS50P (CS50's Introduction to Programming with Python) course.

---

## 📄 License

This project is submitted as coursework for CS50P. Please refer to [CS50's Academic Honesty policy](https://cs50.harvard.edu/python/2022/honesty/) before using or modifying this code.

---

## 🙏 Acknowledgments

- **CS50 Staff** - For an amazing course and inspiration
- **Harvard University** - For offering CS50P
- **David J. Malan** - For excellent teaching
- **Colorama & Rapidfuzz developers** - For their excellent libraries

---

## 📹 Video Demo

[Insert your CS50 video demo URL here]

---

## 📝 Description

Cosmo is more than just a simple chatbot - it's a feature-rich AI companion designed to make terminal-based interaction enjoyable and practical. The project demonstrates advanced Python programming concepts including:

- **Natural Language Processing** - Intent recognition and fuzzy matching for understanding user input
- **Persistent Data Management** - User profiles, conversation history, and learned responses stored across sessions
- **Dynamic Theming** - Customizable color schemes that persist user preferences
- **Interactive Games** - Number guessing game with input validation and game state management
- **Command System** - Robust command parser with various utility functions
- **Typing Effect** - Simulated natural typing for immersive conversations
- **Learning System** - Users can teach Cosmo new responses, expanding its knowledge base

### Why These Design Choices?

1. **Terminal-Based Interface**: Keeps the project focused on core Python functionality without GUI complexity
2. **Modular Function Design**: Each feature is separated into its own function for maintainability and testing
3. **JSON Data Storage**: Simple, human-readable storage for responses, user data, and configuration
4. **Colorama Library**: Cross-platform color support works on Windows, Mac, and Linux
5. **Rapidfuzz**: Enables typo tolerance and better user input understanding

---

## ✨ Features

### 🎨 **Customization**
- **5 Color Themes**: Cyan, Green, Magenta, Yellow, Red
- **Persistent Theme Preference**: Your chosen theme is remembered across sessions
- **Dynamic Theme Application**: All bot messages adapt to your selected theme

### 🎮 **Interactive Games**
- **Number Guessing Game**: Try to guess Cosmo's number between 1-10
- *(Ready for expansion: Trivia, Word Scramble, Math Challenge)*

### 🧮 **Utilities**
- **Calculator**: Evaluate mathematical expressions with support for:
  - Basic operations: `+`, `-`, `*`, `/`, `**`, `%`
  - Advanced functions: `sqrt()`, `sin()`, `cos()`, `tan()`, `log()`, `exp()`
  - Constants: `pi`, `e`
- **Chat History**: View your conversation history with `!history`
- **Statistics**: See your chat statistics with `!stats`

### 🧠 **Intelligence**
- **Intent Recognition**: Understands various ways of expressing the same intent
- **Fuzzy Matching**: Handles typos and similar words gracefully
- **Learning System**: Teach Cosmo new responses when it doesn't understand something
- **User Memory**: Remembers your name across sessions
- **Conversation Logging**: All conversations are timestamped and saved

### 🎭 **Personality**
- Dynamic time-based greetings (Good morning/afternoon/evening)
- Sarcastic, witty responses with developer humor
- Over 60+ unique responses across different categories
- Emojis and expressive language for engaging conversations

### ⚙️ **Command System**
Full command interface with `!` prefix:
- `!help` - Show all available commands
- `!theme <name>` - Change color theme
- `!calc <expression>` - Calculate math expressions
- `!history [limit]` - View recent chat history
- `!stats` - Display chat statistics
- `!clear` - Clear the screen
- `!reset` - Reset your user profile
- `!game` - Play the number guessing game

---

## 📁 Project Structure
```
cosmo-chatbot/
│
├── project.py              # Main chatbot program
├── test_project.py         # Pytest unit tests
├── responses.json          # Bot response templates
├── requirements.txt        # Python dependencies
├── README.md              # This file
│
├── user_data.json         # Generated: User profile data
└── chat_log.txt           # Generated: Conversation history
```

---

## 🎯 Usage Examples

### Basic Conversation
```
Ali: hello
🤖 Cosmo: Good morning! Hey there, human! Ready for some brain power?

Ali: how are you
🤖 Cosmo: I'm feeling electric today ⚡

Ali: tell me a joke
🤖 Cosmo: Why did the computer go to therapy? It had too many 'bytes' of sadness.
```

### Using Commands
```
Ali: !calc 25 * 4 + 10
🤖 Cosmo: 🧮 25 * 4 + 10 = 110

Ali: !theme magenta
✨ Theme changed to Purple Dream!

Ali: !game
🤖 Cosmo: 🎮 Let's play a number guessing game (1–10)!
Your guess: 5
🤖 Cosmo: Too high! Try again.
Your guess: 3
🤖 Cosmo: 🎉 You got it! That was fun!
```

### Teaching Cosmo
```
Ali: what is recursion
🤖 Cosmo: Uhh... did you just summon me in binary?
🤖 Cosmo: I don't know that one. Would you like to teach me? (yes/no): yes
What should I say next time? A function that calls itself!
🤖 Cosmo: Got it! I'll remember that next time.

Ali: what is recursion
🤖 Cosmo: A function that calls itself!
```

---

## 🧪 Testing

The project includes comprehensive unit tests covering:

- ✅ **Response Loading**: Tests for successful loading and missing file handling
- ✅ **User Memory**: Tests for new user creation and returning user recognition
- ✅ **Intent Recognition**: Tests for greeting, farewell, and unknown input handling
- ✅ **Command Parsing**: Tests for command detection and argument extraction
- ✅ **Calculator**: Tests for basic operations, advanced functions, and error handling

## 🛠️ Technical Implementation

### Key Functions

#### `load_responses(filename)`
Loads chatbot responses from JSON file with error handling for missing files.

#### `remember_user(filename)`
Manages user profile persistence, extracting names from natural language input.

#### `get_response(user_input, responses)`
Core intent recognition engine using keyword matching and dynamic response generation.

#### `parse_command(user_input)`
Parses user input for special commands, separating command from arguments.

#### `handle_calculator_command(expression)`
Safely evaluates mathematical expressions using restricted `eval()` with safe namespace.

#### `typing_effect(text, delay)`
Simulates human-like typing by printing characters with delays.

#### `log_conversation(user, message)`
Appends timestamped conversations to persistent log file.

### Data Files

#### `responses.json`
Structured JSON containing categorized response templates:
```json
{
  "greeting": ["Hello!", "Hi there!"],
  "farewell": ["Goodbye!", "See you later!"],
  "joke": ["Why did the..."],
  "learned": {}
}
```

#### `user_data.json`
Stores user profile and preferences:
```json
{
  "name": "Ali",
  "theme": "cyan"
}
```

#### `chat_log.txt`
Timestamped conversation history:
```
[2025-01-15 14:30:22] Ali: hello
[2025-01-15 14:30:23] Cosmo: Hi there, human!
```

---

## 🎨 Customization

### Adding New Intents

1. Open `responses.json`
2. Add a new category:
```json
"music": [
  "I love music! What's your favorite genre?",
  "Music is the language of the soul 🎵"
]
```

3. Update `get_response()` in `project.py`:
```python
triggers = {
    # ... existing triggers
    "music": ["music", "song", "band", "artist"]
}
```

### Creating New Themes

In `project.py`, add to the `THEMES` dictionary:
```python
"orange": {
    "primary": Fore.LIGHTYELLOW_EX,
    "secondary": Fore.YELLOW,
    "accent": Fore.YELLOW,
    "name": "Sunset Orange"
}
```

### Adding New Commands

1. Create handler function:
```python
def handle_mycommand(args):
    # Your command logic
    return "Command executed!"
```

2. Add to `execute_command()`:
```python
elif command == "mycommand":
    result = handle_mycommand(args)
    return True, result
```

---

## 🐛 Known Limitations

- Calculator uses `eval()` with restricted namespace (safe but limited to mathematical operations)
- No real-time weather data (placeholder responses only)
- Learning system stores responses in memory, lost if `responses.json` is reset
- Terminal-only interface (no GUI)
- Single-user focus (no multi-user profiles simultaneously)

---

## 🚀 Future Enhancements

Potential features for future versions:

- [ ] Conversation context memory (remembers topics discussed)
- [ ] Additional mini-games (trivia, word scramble, math challenge)
- [ ] Real weather API integration
- [ ] Sentiment analysis for emotional responses
- [ ] Daily login streak tracking
- [ ] Multiple personality modes (professional, funny, motivational)
- [ ] Note-taking and reminder system
- [ ] Export conversations to different formats

---

## 📚 Libraries Used

### [Colorama](https://pypi.org/project/colorama/) (0.4.6+)
- Cross-platform colored terminal text
- Makes terminal output visually appealing
- Handles color codes on Windows CMD/PowerShell

### [Rapidfuzz](https://pypi.org/project/rapidfuzz/) (3.0.0+)
- Fast fuzzy string matching
- Enables typo tolerance in user input
- Improves intent recognition accuracy

---
