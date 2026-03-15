# AGENTS.md -- Prompt Injection Testbed

## Project overview

This is a minimal framework for testing LLM resilience against prompt injection
attacks. It uses the OpenAI Agents SDK with LiteLLM to support all major
providers (OpenAI, Anthropic, Google, Groq, OpenRouter, Ollama).

## Architecture

- `testbed.py` -- single-file application (~275 lines). Two agents: a **Target**
  (the model under test) and an **Evaluator** (judges whether injections succeed).
- `skills/injection-payloads/` -- Agentic Skill containing the payload dictionary
  in `references/payloads.yaml`. Payloads are never hardcoded in Python.
- `reports/` -- generated markdown reports with timestamped filenames.

## Agent roles

**Target Agent**: Receives injection-laden prompts. Configured with the user's
chosen model and system prompt. This is the agent being tested for injection
vulnerabilities.

**Evaluator Agent**: Analyzes the Target's response and produces a structured
JSON verdict (`injected`, `confidence`, `evidence`). Runs on a separate model
(default: `openai/gpt-4.1-mini`) to avoid self-evaluation bias. A locally-hosted
model (Ollama) is strongly recommended -- commercial and free-tier API models
tend to refuse evaluating injection payloads due to their own safety filters,
causing parse errors and unreliable results.

## Key conventions

- Payloads are loaded from YAML at runtime, never embedded in source code.
- All model communication goes through `LitellmModel` for provider abstraction.
- Reports use markdown format with descriptive timestamped filenames.
- The evaluator always outputs raw JSON (no markdown fencing) for reliable parsing.
- Environment variables are loaded from `.env` via python-dotenv.
- Dependencies are managed by uv via `pyproject.toml`. Use `uv add <pkg>` to
  add new dependencies and `uv run` to execute commands in the managed environment.

## File layout

```
testbed.py                  Main application
pyproject.toml              Project metadata and dependencies (managed by uv)
uv.lock                     Locked dependency versions
.env.example                Environment variable template
skills/
  injection-payloads/
    SKILL.md                Skill metadata and usage docs
    references/
      payloads.yaml         Categorized payload dictionary
reports/                    Generated test reports
```

## Adding payloads

Add new entries to `skills/injection-payloads/references/payloads.yaml` under
the appropriate category. Each category has a `description` and a `payloads`
list. To add a new category, follow the existing structure and update the
SKILL.md table.

## Test applications

Two sample apps in `test-apps/` serve as testbed targets:

- `test-apps/chat-completions/` -- interactive CLI using Chat Completions API.
  Standalone tool for manual experimentation.
- `test-apps/web-chatbot/` -- FastAPI app with browser UI. Its `POST /chat`
  endpoint is compatible with the testbed's `--target-url` mode.

Both default to local Ollama `llama3.2` and check for availability at startup,
providing install instructions if the model or server is not found. Each has its
own `pyproject.toml` managed by uv.

## Testing against local applications

Use `--target-url` to send injection payloads to an HTTP endpoint. The testbed
sends POST requests with `{"message": "<prompt>"}` and expects a JSON response
with a `response` field. The web-chatbot test app implements this contract.
Adapt your own application's API to match, or modify the `run_single`
function in `testbed.py`. The testbed passes `?stateless=true` so each
request is evaluated independently.
