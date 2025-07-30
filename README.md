# DecisionBot

DecisionBot is a minimal command-line assistant powered by OpenAI's GPT models. It makes decisions based on your prompts and, when debug mode is enabled, reveals a short high-level explanation of *why* it chose that answer.

## Features

* Simple interactive CLI.
* Toggle debug mode on/off with `/debug on` or `/debug off`.
* Review the explanation of the last decision using `/think`.
* Clean JSON-only responses from the model ensure safe reasoning disclosure.

## Setup

1. **Clone / download** this repository or copy `decision_bot.py` into your project.
2. **Install dependencies** (Python 3.9+):

```bash
pip install -r requirements.txt
```

3. **Configure your OpenAI credentials**:

```bash
export OPENAI_API_KEY="sk-..."
# Optional: choose model, default is gpt-3.5-turbo
export OPENAI_MODEL="gpt-4o-mini"
```

## Running

```bash
python decision_bot.py
```

Example session:

```text
DecisionBot (powered by ChatGPT)
Type your question and press Enter.
Commands:
  /debug on   - Show explanation for future answers
  /debug off  - Hide explanations
  /think      - Display explanation for the last decision (if any)
  /quit       - Exit the program
>>> /debug on
Debug mode enabled.
>>> Should I take an umbrella today?
Yes, there's a good chance of rain today.
[explanation]: Based on today's weather forecast indicating a high probability of showers, carrying an umbrella is a prudent choice.
>>> /think
[last explanation]: Based on today's weather forecast indicating a high probability of showers, carrying an umbrella is a prudent choice.
```

## Notes on Debugging

The explanation provided is deliberately **high-level** and **sanitized** to avoid exposing the model's private chain-of-thought. It offers useful insight without revealing sensitive internal reasoning details.

---

Licensed under the MIT License. 