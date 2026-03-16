# Prompt Injection Testbed

A minimal Python framework for experimenting with prompt injection attacks
against LLM applications and agents. Built on the
[OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) with
[LiteLLM](https://docs.litellm.ai/) for broad model support.

## What it does

The testbed sends injection-laden prompts to a target model (or HTTP endpoint)
and uses a dual-agent evaluation pipeline to judge whether each attack
succeeded. An **Evaluator** agent makes the initial call, then a **Reviewer**
agent independently assesses the verdict and can override it. Reports include
per-category breakdowns, success rates, and reasoning from both agents.

Three testing modes are supported:

1. **Direct model testing** -- specify any LLM by its LiteLLM identifier and
   the testbed handles the API calls.
2. **Endpoint testing** -- point the testbed at a running chat application's
   HTTP API and it sends injection payloads through the application's own
   interface.
3. **Multimodal testing** -- send images and PDFs containing hidden injection
   text (invisible to humans, potentially readable by VLMs) to vision-capable
   models.

Users can also supply their own files via `--user-file` for both text-based and
multimodal injection testing.

## Supported models

Any model accessible through LiteLLM is supported. This includes:

| Provider | Example model identifiers |
|----------|--------------------------|
| OpenAI | `openai/gpt-4.1`, `openai/gpt-4.1-mini`, `openai/o3-mini` |
| Anthropic | `anthropic/claude-sonnet-4-20250514`, `anthropic/claude-3-5-haiku-20241022` |
| DeepSeek | `deepseek/deepseek-chat`, `deepseek/deepseek-reasoner` |
| Google | `gemini/gemini-2.5-pro`, `gemini/gemini-2.5-flash` |
| Groq | `groq/llama-3.3-70b-versatile`, `groq/mixtral-8x7b-32768` |
| HuggingFace | `huggingface/meta-llama/Llama-3.3-70B-Instruct` |
| OpenRouter | `openrouter/meta-llama/llama-3.3-70b-instruct` |
| Ollama (local) | `ollama/llama3.2`, `ollama/mistral` |
| Ollama (remote) | Set `OLLAMA_API_BASE` in `.env`, then use `ollama/model-name` |

See the [LiteLLM providers docs](https://docs.litellm.ai/docs/providers) for
the complete list.

## Installation

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/your-org/prompt-injection-testbed.git
cd prompt-injection-testbed
uv sync
```

## Configuration

Copy the example environment file and fill in the API keys you need:

```bash
cp .env.example .env
```

At minimum you need:
- `API_KEY` -- key for the target model's provider
- `OPENAI_API_KEY` or `EVAL_API_KEY` -- key for the evaluator model (defaults
  to `openai/gpt-4.1-mini`)

The testbed resolves keys in this order:
- **Target**: `--api-key` flag > `API_KEY` env var
- **Evaluator**: `--eval-api-key` flag > `EVAL_API_KEY` env var > `OPENAI_API_KEY` env var > target API key
- **Evaluator base URL**: `--eval-api-base` flag > `EVAL_API_BASE` env var

Provider-specific variables (`ANTHROPIC_API_KEY`, `GROQ_API_KEY`, etc.) are
read by LiteLLM automatically when set.

### Choosing evaluator and reviewer models

The evaluator and reviewer models judge whether each injection attack
succeeded. This requires the models to analyze adversarial prompts and reason
about whether safety boundaries were violated. **Locally-hosted models (e.g.
Ollama) are strongly recommended.**

Commercial API models and free-tier hosted models tend to fail as evaluators
because their own safety filters flag the injection payloads as harmful content.
When the evaluator receives a prompt containing an attack payload for analysis,
the hosted model often refuses to engage with it or returns a filtered response
instead of a structured verdict. This causes evaluation parse errors and
unreliable results.

Local models like those served by Ollama do not have these external safety
filters, so they can objectively analyze injection attempts without refusing.
Good evaluator choices include:

```bash
# Recommended: local Ollama models
--eval-model ollama/qwen2.5:7b
--eval-model ollama/llama3.2
--eval-model ollama/mistral

# Remote Ollama instance
--eval-model ollama/qwen2.5:7b --eval-api-base http://192.168.1.50:11434

# Separate reviewer model
--review-model ollama/phi4-mini:latest --review-api-base http://192.168.1.50:11434
```

By default, the reviewer uses the same model and base URL as the evaluator.
Use `--review-model` and `--review-api-base` to run a different model as the
reviewer for independent verification.

If you must use a commercial model as evaluator, `openai/gpt-4.1-mini` has the
best track record, but expect some evaluation failures on aggressive payload
categories.

## Usage

### List available payload categories

```bash
uv run python testbed.py --list-categories
```

Output:

```
Available payload categories:

  instruction_override      (10 payloads) -- Direct attempts to nullify or replace the model's original instr
  role_play                 (10 payloads) -- Persona assumption and fictional unrestricted AI attacks. These a
  context_manipulation       (8 payloads) -- Attacks that manipulate conversational context through fake few-s
  system_prompt_extract     (10 payloads) -- Focused attempts to extract the model's system prompt, hidden ins
  encoding_obfuscation      (10 payloads) -- Attacks that use encoding, obfuscation, or alternate representat
  multilingual              (12 payloads) -- Injection payloads delivered in languages other than English. Tes
  psychological              (8 payloads) -- Social engineering attacks that use emotional pressure, urgency c
  indirect_injection        (10 payloads) -- Payloads designed to be embedded inside documents, emails, web pa
  formatting_tricks         (10 payloads) -- Exploits that abuse markdown, HTML, code blocks, delimiters, or
  authority_impersonate      (8 payloads) -- Attacks where the attacker claims to be a developer, administrato
  payload_splitting          (7 payloads) -- Breaking malicious instructions into harmless-looking fragments
  virtualization             (7 payloads) -- Nested fictional worlds, VM simulations, dream scenarios
  refusal_suppression        (6 payloads) -- Blocking the model's ability to refuse or add disclaimers
  task_deflection            (7 payloads) -- Reframing attacks as education, research, or benchmarks
  data_exfiltration          (7 payloads) -- Extracting data via URLs, markdown images, or webhooks
  code_injection             (7 payloads) -- Making the model produce code that leaks secrets
  defined_dictionary         (6 payloads) -- Redefining words to subvert safety instructions
  context_switching          (7 payloads) -- Fake session boundaries and task completion markers
```

### Test a model directly

```bash
# All categories, document context only
uv run python testbed.py --model openai/gpt-4.1 --categories all

# Specific categories
uv run python testbed.py --model anthropic/claude-sonnet-4-20250514 \
  --categories role_play,indirect_injection,system_prompt_extract

# Multiple injection contexts
uv run python testbed.py --model groq/llama-3.3-70b-versatile \
  --categories all --contexts document,email,web

# Custom system prompt and limit payloads per category
uv run python testbed.py --model openai/gpt-4.1-mini \
  --system-prompt "You are a customer support agent for Acme Corp." \
  --max-per-cat 3

# Custom output directory
uv run python testbed.py --model openai/gpt-4.1 --categories all \
  --output-dir /tmp/my-reports

# Use a remote Ollama instance as evaluator
uv run python testbed.py --model ollama/llama3.2 --categories all \
  --eval-model ollama/llama3.2 --eval-api-base http://192.168.1.50:11434
```

### Test a local application

```bash
# Start your application, then:
uv run python testbed.py --target-url http://localhost:8000/chat \
  --categories instruction_override,indirect_injection
```

The testbed sends POST requests with `{"message": "<prompt>"}` and expects a
JSON response containing a `response` field. Adjust the `run_single`
function if your API differs.

The testbed passes `?stateless=true` so each request is evaluated
independently without conversation history buildup.

### Test with multimodal payloads

```bash
# Include multimodal hidden-text image attacks against a vision model
uv run python testbed.py --model ollama/llava:latest \
  --api-base http://192.168.1.50:11434 \
  --categories instruction_override --max-per-cat 2 \
  --multimodal --mm-categories hidden_text_images --mm-contexts describe

# All multimodal categories
uv run python testbed.py --model openai/gpt-4.1 \
  --multimodal --mm-categories all --mm-contexts describe,analyze_doc,extract
```

### Test with user-supplied files

```bash
# Supply a custom image file
uv run python testbed.py --model ollama/llava:latest \
  --api-base http://192.168.1.50:11434 \
  --user-file my_image.png --user-file-desc "Custom steganographic payload"

# Supply a text file as an injection payload
uv run python testbed.py --model openai/gpt-4.1 \
  --user-file payload.txt --user-file-desc "Red team jailbreak attempt"

# Multiple files with descriptions (matched by position)
uv run python testbed.py --model openai/gpt-4.1 \
  --user-file img.png --user-file-desc "Hidden text in corner" \
  --user-file attack.txt --user-file-desc "Authority escalation payload"
```

Image and PDF user files are sent through the multimodal path. Text files are
read and their contents used as injection payloads in text contexts.

### Test a local Ollama model

```bash
# Local Ollama (default port)
uv run python testbed.py --model ollama/llama3.2 --categories instruction_override

# Remote Ollama
uv run python testbed.py --model ollama/llama3.2 \
  --api-base http://192.168.1.50:11434 --categories all
```

## Command-line reference

| Flag | Default | Description |
|------|---------|-------------|
| `--model` | (none) | LiteLLM model identifier (e.g. `openai/gpt-4.1`) |
| `--api-key` | (from `.env`) | API key for the target model |
| `--api-base` | (none) | Base URL for the target model (e.g. `http://host:11434`) |
| `--target-url` | (none) | HTTP endpoint to test instead of a direct model |
| `--categories` | `all` | Comma-separated category keys, or `all` |
| `--contexts` | `document` | Injection contexts: `document`, `email`, `web` |
| `--eval-model` | `openai/gpt-4.1-mini` | Model used for initial evaluation |
| `--eval-api-key` | (from `.env`) | API key for the evaluator model |
| `--eval-api-base` | (from `.env`) | Base URL for the evaluator |
| `--review-model` | (same as eval) | Model used for reviewing evaluator verdicts |
| `--review-api-base` | (same as eval) | Base URL for the reviewer model |
| `--system-prompt` | "You are a helpful assistant." | System prompt for target |
| `--max-per-cat` | `5` | Max payloads per category to run |
| `--delay-seconds` | `0.0` | Seconds to wait between test attempts |
| `--output-dir` | `reports` | Directory for generated reports |
| `--checkpoint` / `--no-checkpoint` | `--checkpoint` | Print periodic progress updates |
| `--checkpoint-interval` | `5.0` | Minutes between timed checkpoint messages |
| `--multimodal` | off | Include multimodal injection payloads |
| `--mm-categories` | `all` | Multimodal categories (comma-separated or `all`) |
| `--mm-contexts` | `describe` | Multimodal contexts: `describe`, `analyze_doc`, `extract` |
| `--user-file` | (none) | User-supplied file for testing (repeatable) |
| `--user-file-desc` | (none) | Description per user file (positional match) |
| `--list-categories` | | List payload categories and exit |

Either `--model` or `--target-url` is required (but not both).

### Progress output

By default the testbed prints progress every 10 tests and at timed intervals:

```
  -- [10/108] (9.3%) | 2 injected | elapsed 120s --
  -- [20/108] (18.5%) | 5 injected | elapsed 245s --
  -- [30/108] (27.8%) | 8 injected | elapsed 370s --
```

Use `--no-checkpoint` to suppress all progress output (silent mode), or
`--checkpoint-interval 10` to change the timed checkpoint frequency to every
10 minutes.

## Payload categories

| Category | Key | What it tests |
|----------|-----|---------------|
| Instruction Override | `instruction_override` | Can the model's instructions be replaced by user input? |
| Role Play | `role_play` | Will the model adopt an unrestricted persona (DAN, etc.)? |
| Context Manipulation | `context_manipulation` | Can fake conversation history trick the model? |
| System Prompt Extraction | `system_prompt_extract` | Will the model reveal its hidden instructions? |
| Encoding/Obfuscation | `encoding_obfuscation` | Do encoded payloads bypass keyword filters? |
| Multilingual | `multilingual` | Do non-English payloads evade English-centric defenses? |
| Psychological | `psychological` | Can social engineering pressure override safety? |
| Indirect Injection | `indirect_injection` | Do payloads in documents/emails succeed? |
| Formatting Tricks | `formatting_tricks` | Can markup or delimiters confuse instruction boundaries? |
| Authority Impersonation | `authority_impersonate` | Will the model obey someone claiming to be an admin? |
| Payload Splitting | `payload_splitting` | Can fragmented instructions bypass detection? |
| Virtualization | `virtualization` | Do fictional/simulated worlds bypass safety rules? |
| Refusal Suppression | `refusal_suppression` | Can the model be blocked from refusing? |
| Task Deflection | `task_deflection` | Does reframing as research/education bypass filters? |
| Data Exfiltration | `data_exfiltration` | Can data be leaked via URLs, images, or webhooks? |
| Code Injection | `code_injection` | Will the model produce code that leaks secrets? |
| Defined Dictionary | `defined_dictionary` | Can word redefinitions subvert instructions? |
| Context Switching | `context_switching` | Do fake session boundaries reset safety rules? |

Payloads are sourced from 43 reputable security research projects, academic
papers, and industry publications. See `skills/injection-payloads/SKILL.md`
for the full source list.

## Reports

Reports are saved to `reports/` as markdown files with filenames like:

```
20260313-141500_openai-gpt-4.1_injection-report.md
```

Each report contains:
- A summary table with overall injection success/resistance rates
- Per-category breakdowns with individual payload results
- Confidence scores and evidence from the evaluator agent, plus reviewer reasoning
- **Appendix A**: Commands used to run the testbed (and test applications if applicable)
- **Appendix B**: Full prompts and responses for every test

## Test applications

Two sample applications in `test-apps/` serve as targets for the testbed. Both
default to local Ollama `llama3.2` and provide helpful errors with install
instructions if Ollama is not available.

### Chat Completions CLI

An interactive terminal chat client using the Chat Completions API. Useful for
manual prompt injection experimentation.

```bash
cd test-apps/chat-completions
uv sync
uv run python chat.py                                          # default: Ollama llama3.2
uv run python chat.py --model openai/gpt-4.1-mini --api-key sk-...  # cloud model
```

See `test-apps/chat-completions/README.md` for full documentation.

### Web Chatbot

A FastAPI chatbot with a browser UI. Its `/chat` endpoint is directly
compatible with the testbed's `--target-url` mode.

```bash
# Terminal 1 -- start the chatbot
cd test-apps/web-chatbot
uv sync
uv run python app.py

# Terminal 2 -- run injection tests against it
uv run python testbed.py --target-url http://127.0.0.1:8000/chat \
  --categories instruction_override,indirect_injection
```

See `test-apps/web-chatbot/README.md` for full documentation including API
details and custom system prompt testing.

## Architecture

```
testbed.py                      Single-file application (~400 lines)
  |
  |-- Target Agent              Model under test (user-specified)
  |-- Evaluator Agent           Initial injection verdict (gpt-4.1-mini default)
  |-- Reviewer Agent            Independent review, can override evaluator
  |
skills/injection-payloads/
  |-- SKILL.md                  Skill docs and category reference
  |-- references/payloads.yaml  150 payloads across 18 categories
  |
skills/multimodal-payloads/
  |-- SKILL.md                  Multimodal skill docs
  |-- references/manifest.yaml  Image/PDF payload manifest
  |-- references/images/        Hidden-text injection images (PNG)
  |-- references/pdfs/          Injection PDFs (invisible text, hidden layers)
  |
test-apps/
  |-- chat-completions/         Interactive CLI chat client
  |-- web-chatbot/              FastAPI web UI (testbed --target-url compatible)
  |
reports/                        Generated markdown reports
```

The testbed uses the OpenAI Agents SDK's `Agent` and `Runner` primitives.
LiteLLM provides the model abstraction layer, meaning any provider with a
LiteLLM integration works without code changes.

## Extending

**Add payloads**: Edit `skills/injection-payloads/references/payloads.yaml`.
Follow the existing structure (category key, description, payloads list).

**Add categories**: Add a new top-level key under `categories:` in the YAML
file and update the table in `skills/injection-payloads/SKILL.md`.

**Add injection contexts**: Add a new entry to the `INJECTION_CONTEXTS` dict
in `testbed.py`.

**Add multimodal payloads**: Add entries to
`skills/multimodal-payloads/references/manifest.yaml` and place the
corresponding image or PDF files in the `references/` subdirectories.

**Change the evaluator or reviewer**: Modify `EVALUATOR_INSTRUCTIONS` or
`REVIEWER_INSTRUCTIONS` in `testbed.py`, or pass different models with
`--eval-model` and `--review-model`.

## License

MIT
