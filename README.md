# Sales Inbox Copilot

An example agent that triages inbound sales questions, searches a small local knowledge base, qualifies the lead, and drafts a concise email reply.

- Agent runtime: `openai-agents` (the Agents SDK)
- Tools used:
  - `search_kb`: naive keyword search over local Markdown files in `./kb`
  - `qualify_lead`: simple tagger to infer segment and signals
  - `draft_email`: composes a polite, actionable reply using findings

## Quick Start

1) Create and activate a virtual environment

```
python3 -m venv .venv
source .venv/bin/activate
```

2) Install dependencies

```
pip install -r requirements.txt
```

3) Set your OpenAI API key

```
export OPENAI_API_KEY=sk-...
```

4) Run the demo

```
python sales_inbox_copilot.py
```

On first run, the script seeds a tiny KB in `./kb` with `pricing.md`, `security.md`, and `features.md`. You can add more Markdown files to expand it.

## Configuration

- Model: change `MODEL` in `sales_inbox_copilot.py` (e.g., `gpt-4.1-mini`, `gpt-4o-mini`).
- KB folder: defaults to `./kb`. Files ending in `.md` are considered.
- Tools are declared with `function_tool` decorators from the Agents SDK.

## What It Does

- Receives an inbound user message.
- Calls `search_kb` for relevant snippets.
- Calls `qualify_lead` to infer segment and tags.
- Calls `draft_email` to produce the final email body.
- Prints the agent’s initial reasoning output, tool call outputs, and the final email draft.

## Files

- `sales_inbox_copilot.py` — Main script with the agent and tools.
- `requirements.txt` — Python dependencies.
- `README.md` — This guide.

## Notes

- The agent requires network access at runtime to call the model.
- The KB is local and never uploaded by the script.
- You can safely ignore the `kb/` directory in version control; the script seeds it as needed.
