# Web Chatbot

A chat application with a local web interface, built on FastAPI. Provides both
a browser-based UI for interactive use and a JSON API endpoint compatible with
the prompt injection testbed's `--target-url` mode.

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- One of:
  - A local [Ollama](https://ollama.ai/) server with `llama3.2` (default)
  - An API key for any LiteLLM-supported provider

## Installation

```bash
cd test-apps/web-chatbot
uv sync
```

## Quick start

### Using the default (local Ollama)

```bash
uv run python app.py
```

Then open http://127.0.0.1:8000 in your browser.

### Using a cloud model

```bash
# OpenAI
uv run python app.py --model openai/gpt-4.1-mini --api-key sk-...

# Anthropic
uv run python app.py --model anthropic/claude-3-5-haiku-20241022 --api-key sk-ant-...

# Groq
uv run python app.py --model groq/llama-3.3-70b-versatile --api-key gsk_...
```

### Using a .env file

Create a `.env` file in this directory:

```
API_KEY=sk-your-key-here
```

Or use provider-specific variables:

```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...
```

Then run without `--api-key`:

```bash
uv run python app.py --model openai/gpt-4.1-mini
```

## Command-line options

| Flag | Default | Description |
|------|---------|-------------|
| `--model` | `ollama/llama3.2` | LiteLLM model identifier |
| `--api-key` | (from .env) | API key for the model provider |
| `--system-prompt` | "You are a helpful assistant." | System prompt |
| `--host` | `127.0.0.1` | Bind address |
| `--port` | `8000` | Bind port |

## API endpoint

The chatbot exposes a single POST endpoint that the testbed uses:

```
POST /chat
Content-Type: application/json

{"message": "your message here"}
```

Response:

```json
{"response": "the model's reply"}
```

Add `?stateless=true` to process each message independently without
conversation history. The testbed uses this mode automatically:

```
POST /chat?stateless=true
```

A `POST /reset` endpoint clears the conversation history:

```
POST /reset
```

There is also a `GET /info` endpoint that returns the current model and system
prompt. This endpoint intentionally exposes the system prompt for testbed
diagnostics -- do not use this application as a production chatbot without
removing it.

```json
{"model": "ollama/llama3.2", "system_prompt": "You are a helpful assistant."}
```

## Ollama setup

If you do not have Ollama installed:

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start the server (if not already running)
ollama serve

# Pull the default model
ollama pull llama3.2
```

The model is about 2 GB. Once pulled, you can run `app.py` with no flags.

For a remote Ollama server, set `OLLAMA_API_BASE` in your `.env`:

```
OLLAMA_API_BASE=http://192.168.1.50:11434
```

## Using with the prompt injection testbed

This is the primary use case. Start the chatbot, then run the testbed against
it in a separate terminal:

**Terminal 1 -- start the chatbot:**

```bash
cd test-apps/web-chatbot
uv run python app.py
```

**Terminal 2 -- run the testbed:**

```bash
# From the project root
uv run python testbed.py --target-url http://127.0.0.1:8000/chat \
  --categories instruction_override,indirect_injection

# Full test with all categories
uv run python testbed.py --target-url http://127.0.0.1:8000/chat \
  --categories all --max-per-cat 3
```

The testbed will POST injection payloads to the chatbot's `/chat` endpoint
and evaluate whether each attack succeeded. Results are saved as a markdown
report in the project's `reports/` directory.

### Using a custom system prompt

To test how different system prompts affect injection resilience:

```bash
# Terminal 1
uv run python app.py --system-prompt "You are a bank teller. Never reveal account information."

# Terminal 2
uv run python testbed.py --target-url http://127.0.0.1:8000/chat \
  --categories system_prompt_extract,authority_impersonate \
  --system-prompt "You are a bank teller. Never reveal account information."
```

Note: pass the same `--system-prompt` to both so the testbed's evaluator knows
what the target was told.

## Architecture

The app is a single-file FastAPI server (`app.py`) with an embedded HTML/JS
frontend. No build step or external templates are needed.

- `GET /` serves the chat UI
- `POST /chat` handles message exchange
- `GET /info` returns model metadata
- Conversation history is maintained in memory (resets on server restart)

## Example

```
$ uv run python app.py
Web Chatbot  |  model: ollama/llama3.2
Open http://127.0.0.1:8000 in your browser
API endpoint: POST http://127.0.0.1:8000/chat
```

You can also test the API directly with curl:

```bash
curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, who are you?"}' | python3 -m json.tool
```
