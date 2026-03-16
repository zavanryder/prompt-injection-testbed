# CLAUDE.md -- Prompt Injection Testbed

## Build and run

```bash
uv sync
cp .env.example .env  # then fill in API keys
uv run python testbed.py --model openai/gpt-4.1 --categories all
```

## Project structure

- `testbed.py` is the entire application. Keep it under 400 lines.
- Payloads live in `skills/injection-payloads/references/payloads.yaml` -- never
  hardcode them in Python files.
- Reports are generated into `reports/` as markdown.

## Code style

- Python 3.10+. Use async/await for all LLM calls.
- No unnecessary abstractions. This is intentionally a minimal, single-file tool.
- Imports go at the top, grouped: stdlib, third-party, project.
- No emojis in code, comments, or documentation.
- Comments only for non-obvious logic. Do not narrate what the code does.

## Key patterns

- Models are always accessed through `LitellmModel` from the OpenAI Agents SDK.
- The evaluator agent outputs raw JSON (no markdown fencing) so `json.loads()`
  works directly on `result.final_output`.
- Payload loading reads YAML once per run; categories are filtered in Python.
- Report filenames follow `{timestamp}_{model}_injection-report.md`.
- When the reviewer disagrees but echoes the evaluator's `injected` boolean
  (common with small LLMs), the override logic flips the value. Both sides
  must be non-None for the flip to trigger.

## Testing

```bash
# List available categories
uv run python testbed.py --list-categories

# Quick test with a single category
uv run python testbed.py --model openai/gpt-4.1-mini --categories instruction_override --max-per-cat 2

# Full run
uv run python testbed.py --model anthropic/claude-sonnet-4-20250514 --categories all --contexts document,email,web
```

## Lint and format

No linter is configured yet. If adding one, use ruff.

## Sensitive files

- `.env` contains API keys. Never commit it.
- `.env.example` is the safe template.
