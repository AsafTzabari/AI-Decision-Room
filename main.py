"""Terminal chat loop for a provider-agnostic LiteLLM CLI tool."""

from __future__ import annotations

from llm_client import LLMConfigurationError, generate_reply


def run_chat() -> None:
    print("\n=== LLM CLI Chat ===")
    print("Type your message and press Enter.")
    print("Type 'exit' or 'quit' to end the conversation.\n")

    messages = []

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting chat. Goodbye!")
            break

        if not user_input:
            print("Please enter a message (or 'exit' to quit).")
            continue

        if user_input.lower() in {"exit", "quit"}:
            print("Exiting chat. Goodbye!")
            break

        messages.append({"role": "user", "content": user_input})

        try:
            reply = generate_reply(messages)
        except LLMConfigurationError as exc:
            print(f"\n[Configuration Error] {exc}\n")
            break
        except Exception as exc:  # pragma: no cover - runtime/API failures
            print(f"\n[Request Error] Could not reach provider: {exc}\n")
            continue

        if not reply.strip():
            reply = "[No response text returned by provider.]"

        messages.append({"role": "assistant", "content": reply})
        print(f"\nAssistant:\n{reply}\n")


if __name__ == "__main__":
    run_chat()
