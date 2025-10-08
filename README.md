# OpenAIagentDemo – Sales Inbox Copilot
Email response/triage tool built with the OpenAI Agents SDK.

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

Or copy `.env.example` to `.env` and add your key (if using python-dotenv).

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
- Prints the agent's initial reasoning output, tool call outputs, and the final email draft.

## Example Interaction

**Input message:**
```
Hi, we are evaluating your platform for a 120 person research team.
Do you support SSO with Okta and can we export results to CSV?
We need SOC 2 and ISO docs for security review.
```

**Agent's response:**
```
--- Agent initial response ---
I'll search the knowledge base and qualify this lead to draft an appropriate response.

[Tool called] search_kb
{
  "results": [
    {
      "path": "./kb/security.md",
      "score": 6,
      "snippet": "# Security We support SSO via Okta and Azure AD. Data is encrypted at rest and in transit. We offer SOC 2 Type II and ISO 27001 reports on request."
    },
    {
      "path": "./kb/features.md",
      "score": 3,
      "snippet": "# Features Realtime search over earnings, filings, news, and expert insights. Exports to CSV, PDF, and Slack. Native integrations for Salesforce and Snowflake."
    }
  ]
}

[Tool called] qualify_lead
{
  "segment": "enterprise",
  "tags": ["security/enterprise", "large-team"]
}

--- Draft email ---
Hi there,

Thanks for reaching out and for the details below.

Here is a quick answer and next steps:

Key points
- security.md: # Security We support SSO via Okta and Azure AD. Data is encrypted at rest and in transit. We offer SOC 2 Type II and ISO 27001 reports on request.
- features.md: # Features Realtime search over earnings, filings, news, and expert insights. Exports to CSV, PDF, and Slack. Native integrations for Salesforce and Snowflake.

Based on what you shared, I recommend our Enterprise plan.
If helpful, I can also share security documentation.

Would you like a 20 minute call this week to tailor a trial and answer questions?

Best,
Your Name
```

The agent automatically:
- Identifies security and export-related questions
- Searches the knowledge base for relevant documentation
- Qualifies the lead as "enterprise" based on SSO requirements and team size
- Drafts a personalized response with relevant details

## Testing

Run the unit tests to verify the tool functions:

```
python -m unittest test_sales_inbox_copilot.py
```

The test suite covers:
- Knowledge base search functionality
- Lead qualification logic
- Email drafting
- Error handling for edge cases

## Files

- `sales_inbox_copilot.py` — Main script with the agent and tools.
- `test_sales_inbox_copilot.py` — Unit tests for the tool functions.
- `requirements.txt` — Python dependencies.
- `.env.example` — Template for environment variables.
- `README.md` — This guide.

## Notes

- The agent requires network access at runtime to call the model.
- The KB is local and never uploaded by the script.
- You can safely ignore the `kb/` directory in version control; the script seeds it as needed.
