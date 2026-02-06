# Autonomous Incident Commander

Agentic incident investigation: detect latency spikes, gather metrics/logs/deployments, and run causal reasoning to recommend rollback. **HTML/CSS/JS** UI with **chat** (LLM can decide and act) and **dashboard**.

## Setup

```bash
poetry install
```

Optional: set `OPENAI_API_KEY` or Azure OpenAI env vars (`AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_VERSION`, `AZURE_OPENAI_CHAT_DEPLOYMENT`) for the LLM chat.

## Run the web UI

```bash
poetry run uvicorn main:app --reload
```

Open http://localhost:8000 .

## Features

- **Dashboard:** Status, verdict (e.g. ROLLBACK RECOMMENDED), investigation feed, and RCA report. Use **Simulate incident** to run the pipeline and populate the dashboard.
- **Chat:** Ask the Commander in natural language. The **LLM can decide and act**: it can run the full investigation, fetch metrics, search logs, or list deployments via tools, then respond with reasoning and recommendation. If the LLM runs an investigation, the dashboard updates automatically.

## Demo flow

1. Click **Simulate incident** to run the pipeline and see the verdict and RCA.
2. In **Chat**, try: *"What caused the latency spike?"* or *"Should we rollback?"* — the LLM can run the investigation and answer.
3. Dashboard shows investigation feed and ROLLBACK RECOMMENDED when DEP-9921 is identified as root cause.

## Project layout

- `data/` — Mock `metrics.json`, `logs.json`, `deployments.json` (latent config bug timeline).
- `agents/` — Specialist tools and Commander causal logic.
- `engine.py` — IncidentState, trigger check, state machine (Gather → Reason).
- `main.py` — FastAPI app: serves HTML UI and API (`/api/status`, `/api/simulate-incident`, `/api/state`, `/api/query`).
- `static/` — `index.html`, `styles.css`, `app.js` for chat and dashboard.
- `llm_agent.py` — LLM with tools (run_full_investigation, get_metrics, search_logs_tool, get_recent_deployments_tool); used by `/api/query`.
- `rca.py` — RCA report generator.
- `app.py` — Legacy Streamlit UI (optional; primary UI is the web app above).
