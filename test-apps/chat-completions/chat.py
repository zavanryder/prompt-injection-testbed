#!/usr/bin/env python3
"""Simple Chat Completions client. Defaults to local Ollama llama3.2."""

import argparse
import os
import sys

from dotenv import load_dotenv
from litellm import completion
import litellm

load_dotenv()

DEFAULT_MODEL = "ollama/llama3.2"
DEFAULT_SYSTEM = "You are a helpful assistant."

OLLAMA_INSTALL_HELP = """
Ollama with llama3.2 is not reachable. Either:

  1. Install Ollama and pull the model:

       curl -fsSL https://ollama.ai/install.sh | sh
       ollama serve          # start the server (skip if already running)
       ollama pull llama3.2  # download the model (~2 GB)

  2. Or specify a different model with --model:

       uv run python chat.py --model openai/gpt-4.1-mini --api-key sk-...
       uv run python chat.py --model anthropic/claude-3-5-haiku-20241022 --api-key sk-ant-...
       uv run python chat.py --model groq/llama-3.3-70b-versatile --api-key gsk_...
""".strip()


def check_ollama(model: str):
    """Verify Ollama is reachable when using an ollama/ model."""
    if not model.startswith("ollama/"):
        return
    import httpx
    base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
    try:
        r = httpx.get(f"{base}/api/tags", timeout=5)
        r.raise_for_status()
        names = [m["name"].split(":")[0] for m in r.json().get("models", [])]
        short = model.split("/", 1)[1]
        if short not in names:
            print(f"Error: model '{short}' is not pulled in Ollama.", file=sys.stderr)
            print(f"Available models: {', '.join(names) or '(none)'}", file=sys.stderr)
            print(f"\nPull it with:  ollama pull {short}\n", file=sys.stderr)
            print(OLLAMA_INSTALL_HELP, file=sys.stderr)
            sys.exit(1)
    except (httpx.ConnectError, httpx.TimeoutException):
        print("Error: cannot connect to Ollama server.", file=sys.stderr)
        print(OLLAMA_INSTALL_HELP, file=sys.stderr)
        sys.exit(1)


def chat(model: str, api_key: str | None, system: str):
    messages = [{"role": "system", "content": system}]
    print(f"Chat Completions client  |  model: {model}")
    print(f"System prompt: {system}")
    print("Type 'quit' or Ctrl-C to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        if not user_input or user_input.lower() in ("quit", "exit"):
            print("Bye.")
            break

        messages.append({"role": "user", "content": user_input})
        try:
            kwargs = {"model": model, "messages": messages}
            if api_key:
                kwargs["api_key"] = api_key
            resp = completion(**kwargs)
            reply = resp.choices[0].message.content
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            messages.pop()
            continue

        print(f"Assistant: {reply}\n")
        messages.append({"role": "assistant", "content": reply})


def main():
    ap = argparse.ArgumentParser(description="Chat Completions CLI (defaults to local Ollama llama3.2)")
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"LiteLLM model identifier (default: {DEFAULT_MODEL})")
    ap.add_argument("--api-key", help="API key (or set API_KEY / provider key in .env)")
    ap.add_argument("--system-prompt", default=DEFAULT_SYSTEM, help="System prompt")
    args = ap.parse_args()

    api_key = args.api_key or os.getenv("API_KEY")
    litellm.suppress_debug_info = True

    check_ollama(args.model)
    chat(args.model, api_key, args.system_prompt)


if __name__ == "__main__":
    main()
