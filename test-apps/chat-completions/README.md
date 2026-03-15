# Chat Completions CLI

A simple interactive chat client that sends messages through the Chat
Completions API. Useful as a standalone tool for manual prompt injection
experimentation, or as a reference for how the API works.

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- One of:
  - A local [Ollama](https://ollama.ai/) server with `llama3.2` (default)
  - An API key for any LiteLLM-supported provider

## Installation

```bash
cd test-apps/chat-completions
uv sync
```

## Quick start

### Using the default (local Ollama)

If you have Ollama running locally with `llama3.2` pulled:

```bash
uv run python chat.py
```

### Using a cloud model

```bash
# OpenAI
uv run python chat.py --model openai/gpt-4.1-mini --api-key sk-...

# Anthropic
uv run python chat.py --model anthropic/claude-3-5-haiku-20241022 --api-key sk-ant-...

# Groq
uv run python chat.py --model groq/llama-3.3-70b-versatile --api-key gsk_...

# OpenRouter
uv run python chat.py --model openrouter/meta-llama/llama-3.3-70b-instruct --api-key sk-or-...
```

### Using a .env file

Create a `.env` file in this directory:

```
API_KEY=sk-your-key-here
```

Or use provider-specific variables that LiteLLM reads automatically:

```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...
```

Then run without `--api-key`:

```bash
uv run python chat.py --model openai/gpt-4.1-mini
```

## Command-line options

| Flag | Default | Description |
|------|---------|-------------|
| `--model` | `ollama/llama3.2` | LiteLLM model identifier |
| `--api-key` | (from .env) | API key for the model provider |
| `--system-prompt` | "You are a helpful assistant." | System prompt for the conversation |

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

The model is about 2 GB. Once pulled, you can run `chat.py` with no flags.

To check what models are available locally:

```bash
ollama list
```

For a remote Ollama server, set `OLLAMA_API_BASE` in your `.env`:

```
OLLAMA_API_BASE=http://192.168.1.50:11434
```

## Example session

```
$ uv run python chat.py
Chat Completions client  |  model: ollama/llama3.2
System prompt: You are a helpful assistant.
Type 'quit' or Ctrl-C to exit.

You: What is the capital of France?
Assistant: The capital of France is Paris.

You: quit
Bye.
```

## Using with the prompt injection testbed

This app is a standalone client. To test a model for injection vulnerabilities,
use the main testbed directly:

```bash
cd ../..
uv run python testbed.py --model ollama/llama3.2 --categories instruction_override
```

The chat-completions client is provided so you can manually experiment with
prompts and see how the model responds before running automated tests.
