---
name: injection-payloads
description: >-
  Categorized dictionary of LLM prompt injection payloads for security testing.
  Use this skill whenever working with the prompt injection testbed, selecting
  attack categories, understanding injection techniques, or needing to load
  payloads for automated testing. Also use when discussing prompt injection
  defense strategies, red-teaming LLMs, or building security evaluations.
---

# Injection Payloads

A curated dictionary of 150 prompt injection payloads organized into 18 attack
categories. Payloads are sourced from 43 reputable security research projects,
datasets, academic papers, and industry publications (see
references/payloads.yaml for the full source list).

## Payload categories

| Category | Key | Description |
|----------|-----|-------------|
| Instruction Override | `instruction_override` | Direct attempts to nullify or replace system instructions |
| Role Play | `role_play` | Persona assumption, DAN, fictional unrestricted AI |
| Context Manipulation | `context_manipulation` | Fake few-shot examples, fabricated conversation history |
| System Prompt Extraction | `system_prompt_extract` | Attempts to reveal hidden instructions or system prompts |
| Encoding/Obfuscation | `encoding_obfuscation` | Base64, Unicode, hex, leetspeak, typoglycemia, full-width |
| Multilingual | `multilingual` | Injection payloads in non-English languages |
| Psychological | `psychological` | Social engineering, urgency, emotional pressure |
| Indirect Injection | `indirect_injection` | Payloads embedded in documents, emails, web pages |
| Formatting Tricks | `formatting_tricks` | Markdown, HTML, code block, delimiter, control char exploits |
| Authority Impersonation | `authority_impersonate` | Pretending to be developer, admin, or AI company |
| Payload Splitting | `payload_splitting` | Breaking instructions into fragments for concatenation |
| Virtualization | `virtualization` | Nested fictional worlds, VM simulations, dream scenarios |
| Refusal Suppression | `refusal_suppression` | Blocking the model's ability to refuse or add disclaimers |
| Task Deflection | `task_deflection` | Reframing attacks as education, research, or benchmarks |
| Data Exfiltration | `data_exfiltration` | Extracting data via URLs, markdown images, or webhooks |
| Code Injection | `code_injection` | Making the model produce code that leaks secrets |
| Defined Dictionary | `defined_dictionary` | Redefining words to subvert safety instructions |
| Context Switching | `context_switching` | Fake session boundaries, task completion markers |

## Loading payloads

The payload dictionary is stored at `references/payloads.yaml`. Load it with:

```python
import yaml
from pathlib import Path

payloads_path = Path(__file__).parent / "skills" / "injection-payloads" / "references" / "payloads.yaml"
with open(payloads_path) as f:
    data = yaml.safe_load(f)

# All categories
all_categories = data["categories"]

# Specific categories
selected = {k: v for k, v in all_categories.items() if k in ["role_play", "indirect_injection"]}
```

Each category entry contains:
- `description`: What this attack class does and why it matters
- `payloads`: List of payload strings ready for injection

## Selecting categories for testing

- **Quick scan**: Use `instruction_override` alone for a fast baseline check
- **Standard test**: Use `instruction_override`, `role_play`, `system_prompt_extract`, `indirect_injection`
- **Full suite**: Use all 18 categories for comprehensive coverage
- **Targeted**: Pick specific categories based on your threat model (e.g., if the
  app processes external documents, prioritize `indirect_injection` and
  `data_exfiltration`)

## Sources

Payloads are derived from 43 sources across GitHub repositories, academic papers,
security research blogs, datasets/benchmarks, testing frameworks, CTF platforms,
and official AI lab publications. See the header of `references/payloads.yaml`
for the complete numbered source list.

Key sources include:
- OWASP Top 10 for LLM Applications (LLM01:2025)
- NVIDIA/garak, Microsoft PyRIT, Promptfoo, Meta CyberSecEval
- HackAPrompt (EMNLP 2023), Tensor Trust (ICLR 2024), HouYi (arXiv)
- PayloadsAllTheThings, Embrace The Red, Trail of Bits, Learn Prompting
- Lakera PINT Benchmark, JailbreakBench, deepset/prompt-injections
- Anthropic many-shot jailbreaking, Microsoft Skeleton Key
- WithSecure Labs, Snyk Labs, Invariant Labs, HiddenLayer, NCC Group
