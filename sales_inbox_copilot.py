# Demo: Agent with 3 tools to handle inbound product questions and draft replies.

import os, re, glob, json
from typing import List, Dict

# Agents SDK imports
from agents import Agent, Handoff, Session  # provided by `openai-agents`
from agents.tool import function_tool

MODEL = "gpt-4.1-mini"  # pick a fast reasoning model you have access to

# --- Simple local knowledge base loader ---
KB_DIR = "./kb"
os.makedirs(KB_DIR, exist_ok=True)

# Seed a few example files if the folder is empty
if not glob.glob(f"{KB_DIR}/*.md"):
    seed_docs = {
        "pricing.md": """# Pricing
Our Pro plan is 99 USD per seat per month. Annual discount available at 15 percent.
Enterprise plans include SSO, advanced audit logs, and custom SLAs.""",
        "security.md": """# Security
We support SSO via Okta and Azure AD. Data is encrypted at rest and in transit.
We offer SOC 2 Type II and ISO 27001 reports on request.""",
        "features.md": """# Features
Realtime search over earnings, filings, news, and expert insights.
Exports to CSV, PDF, and Slack. Native integrations for Salesforce and Snowflake."""
    }
    for name, text in seed_docs.items():
        with open(os.path.join(KB_DIR, name), "w", encoding="utf-8") as f:
            f.write(text)


def simple_search(files: List[str], query: str, top_k: int = 3) -> List[Dict]:
    # naive keyword ranker that is good enough for the demo
    q_terms = [t.lower() for t in re.findall(r"\w+", query)]
    hits = []
    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            txt = f.read()
        score = sum(txt.lower().count(t) for t in q_terms)
        if score > 0:
            # return a short snippet
            snippet = txt[:400].strip().replace("\n", " ")
            hits.append({"path": path, "score": score, "snippet": snippet})
    return sorted(hits, key=lambda x: x["score"], reverse=True)[:top_k]


# --- Define tools ---

@function_tool(
    name_override="search_kb",
    description_override="Search the local knowledge base for content answering the user's question.",
)
def search_kb(query: str, top_k: int = 3) -> Dict:
    files = glob.glob(f"{KB_DIR}/*.md")
    results = simple_search(files, query, top_k=top_k)
    return {"results": results}


@function_tool(
    name_override="qualify_lead",
    description_override="Classify the inbound message as enterprise, pro, or not-a-lead and extract basic qualifiers.",
)
def qualify_lead(message: str) -> Dict:
    tags = []
    if re.search(r"SSO|Okta|Azure AD|SAML|SOC 2|ISO 27001", message, re.I):
        tags.append("security/enterprise")
    if re.search(r"\bPOC|trial|pilot\b", message, re.I):
        tags.append("buying-signal")
    if re.search(r"\b(> ?100|100\+|over 100|seats)\b", message, re.I):
        tags.append("large-team")
    if not tags:
        tags.append("general")
    segment = "enterprise" if "security/enterprise" in tags or "large-team" in tags else "pro"
    return {"segment": segment, "tags": tags}


@function_tool(
    name_override="draft_email",
    description_override="Draft a polite email reply using lead qualifiers and KB snippets.",
    strict_mode=False,
)
def draft_email(customer_name: str, customer_message: str, lead: Dict, kb_snippets: List[Dict]) -> Dict:
    # The agent will usually write this text, but we keep a server-side guardrail template here too.
    bullets = []
    for r in kb_snippets[:3]:
        bullets.append(f"- {os.path.basename(r['path'])}: {r['snippet']}")
    body = f"""Hi {customer_name},

Thanks for reaching out and for the details below.

Here is a quick answer and next steps:

Key points
{chr(10).join(bullets) if bullets else "- We will share details on a short call."}

Based on what you shared, I recommend our {lead.get('segment','pro').title()} plan. 
If helpful, I can also share security documentation.

Would you like a 20 minute call this week to tailor a trial and answer questions?

Best,
Your Name
"""
    return {"email_body": body}


# --- Make the agent ---

agent = Agent(
    name="Sales Inbox Copilot",
    instructions=(
        "You are a helpful sales assistant. "
        "When a new inbound message arrives, first search_kb with the user's text. "
        "Then run qualify_lead on the same text. "
        "Finally call draft_email using the results to produce a reply. "
        "Keep replies concise and friendly. Cite product facts plainly."
    ),
    model=MODEL,
    tools=[search_kb, qualify_lead, draft_email],
)


def demo_run():
    session: Session = agent.new_session(metadata={"demo": "sales_inbox"})
    user_msg = (
        "Hi, we are evaluating your platform for a 120 person research team. "
        "Do you support SSO with Okta and can we export results to CSV? "
        "We need SOC 2 and ISO docs for security review."
    )
    print("\n--- Incoming message ---\n", user_msg)

    # Step 1: let the agent think and choose tools
    r1 = session.run(user_msg)
    print("\n--- Agent initial response ---\n", r1.output_text)

    # For inspection, show tool call outputs the agent used
    for call in r1.tool_calls:
        print(f"\n[Tool called] {call.name}")
        print(json.dumps(call.output, indent=2))

    # Step 2: ask the agent for the final email
    r2 = session.run("Please provide the final email reply only.")
    print("\n--- Draft email ---\n", r2.output_text)


if __name__ == "__main__":
    # Requires OPENAI_API_KEY to be set in the environment
    # Example: export OPENAI_API_KEY=sk-...
    demo_run()
