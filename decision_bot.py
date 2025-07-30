import os
import json
import sys
from typing import Optional

import openai

# Default model can be overridden via the OPENAI_MODEL env var
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

SYSTEM_PROMPT = (
    "You are DecisionGPT, an AI assistant that helps users make decisions. "
    "Respond ONLY with valid JSON containing exactly two keys: "
    "'decision' (your answer to the user) and 'explanation' (a SHORT, high-level rationale). "
    "Do NOT reveal private chain-of-thought or hidden reasoning."
)


class DecisionBot:
    """Simple wrapper around the OpenAI ChatCompletion API that optionally exposes
    short explanations for decisions when debug mode is enabled.
    """

    def __init__(self, model: str = DEFAULT_MODEL, debug: bool = False):
        self.model: str = model
        self.debug: bool = debug
        self.last_explanation: Optional[str] = None

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------
    def toggle_debug(self, value: bool) -> None:
        """Enable or disable debug mode."""
        self.debug = value
        if not value:
            # Clear cached explanation when turning debug off
            self.last_explanation = None

    def get_decision(self, prompt: str) -> str:
        """Send *prompt* to the model and return its decision. If debug mode is
        active, also capture the short explanation in ``self.last_explanation``.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        response = openai.ChatCompletion.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
        )

        assistant_raw = response.choices[0].message["content"].strip()
        decision, explanation = self._parse_json_response(assistant_raw)
        self.last_explanation = explanation

        # If debug is disabled, discard explanation for the caller
        return decision

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_json_response(text: str):
        """Attempt to parse the assistant response as JSON.

        Falls back gracefully if the model returns malformed JSON by best-effort
        extraction of the 'decision' key.
        """
        try:
            payload = json.loads(text)
            decision = payload.get("decision", "[No decision provided]")
            explanation = payload.get("explanation")
        except json.JSONDecodeError:
            # Fallback: treat entire text as decision
            decision, explanation = text, None
        return decision, explanation


# -------------------------------------------------------------------------
# Simple interactive CLI
# -------------------------------------------------------------------------

def _print_banner() -> None:
    banner = (
        "DecisionBot (powered by ChatGPT)\n"
        "Type your question and press Enter.\n"
        "Commands:\n"
        "  /debug on   - Show explanation for future answers\n"
        "  /debug off  - Hide explanations\n"
        "  /think      - Display explanation for the last decision (if any)\n"
        "  /quit       - Exit the program\n"
    )
    print(banner)


def main(argv: list[str] | None = None) -> None:  # noqa: D401
    """Entry point for running the bot as a CLI application."""
    _print_banner()
    bot = DecisionBot(debug=False)

    while True:
        try:
            user_input = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            continue

        # Handle commands ---------------------------------------------------
        if user_input.lower() in {"/quit", "quit", "exit"}:
            print("Goodbye.")
            break

        if user_input.startswith("/debug"):
            parts = user_input.split(maxsplit=1)
            flag = parts[1].lower() if len(parts) == 2 else "on"
            bot.toggle_debug(flag == "on")
            state = "enabled" if bot.debug else "disabled"
            print(f"Debug mode {state}.")
            continue

        if user_input.startswith("/think"):
            if bot.last_explanation:
                print(f"[last explanation]: {bot.last_explanation}")
            else:
                print("No explanation available. Enable debug mode and ask a question first.")
            continue

        # Regular prompt ----------------------------------------------------
        decision = bot.get_decision(user_input)
        print(decision)

        if bot.debug and bot.last_explanation:
            print("[explanation]:", bot.last_explanation)


if __name__ == "__main__":
    main()