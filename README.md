# ClearPath — Clinical Prior Authorization Agent

> Prior authorization costs US hospitals **$13B/year** in administrative overhead. ClearPath cuts turnaround from days to minutes using an AI agent powered by Azure OpenAI GPT-4.1.

Built at **Musa Labs Hackathon SF — Enterprise Agents** (Feb 27, 2026)

## What It Does

ClearPath is an AI agent that automates the clinical prior authorization workflow:

1. **Ingests a patient case** — diagnosis codes (ICD-10), procedure codes (CPT), and clinical notes
2. **Looks up payer-specific requirements** — RAG over insurance policy documents (United Healthcare, Aetna, BCBS)
3. **Drafts the authorization request** — formal letter with clinical justification
4. **Predicts approval likelihood** — confidence scoring with strengths, risks, and missing documentation
5. **Routes to human reviewer** — when confidence < 70% (responsible AI, human-in-the-loop)

## Architecture

```
Patient Case Input
       ↓
Azure OpenAI GPT-4.1 — Clinical reasoning agent
       ↓
5-Tool Pipeline (function calling):
  ┌─ extract_diagnosis()      → ICD-10/CPT validation
  ├─ lookup_payer_policy()    → Payer requirement lookup (RAG)
  ├─ draft_auth_request()     → Structured authorization letter
  ├─ predict_approval()       → Confidence score + gap analysis
  └─ route_to_human()         → HITL if confidence < 70%
       ↓
Output: Auth request + approval prediction + full audit trail
```

## Azure Services

- **Azure OpenAI** — GPT-4.1 for multi-step clinical reasoning
- **Azure AI Foundry** — Model deployment and management
- **Microsoft Agent Framework** — Agent orchestration patterns

## Tech Stack

- **Backend**: Python, FastAPI, OpenAI SDK
- **Frontend**: React (CDN), single-page dashboard
- **Agent**: Azure OpenAI function calling with 5 clinical tools

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your Azure OpenAI credentials to .env

# Run the server
python main.py
```

Open **http://localhost:8080** in your browser.

## Demo Flow

1. Click a **sample case** (e.g., Maria Rodriguez — Total Knee Replacement)
2. Hit **Submit for Prior Authorization**
3. Watch the agent execute all 5 tools in sequence (~10 seconds)
4. Review the **authorization letter**, **confidence score**, and **agent trace**
5. Submit a borderline case to see **human-in-the-loop routing**

## Sample Cases Included

| Patient | Procedure | Payer | Expected Outcome |
|---------|-----------|-------|-------------------|
| Maria Rodriguez, 67F | Total Knee Replacement | United Healthcare | High confidence (~92%) — strong documentation |
| James Thompson, 52M | MRI Lumbar Spine | Aetna | Medium confidence — conservative tx only 8 weeks |
| Robert Kim, 71M | MRI Brain | Blue Cross Blue Shield | High confidence — red flag symptoms present |

## Key Features

- **Multi-step agent reasoning** — 5 tools called sequentially with context passing
- **Payer-specific policy lookup** — Different requirements per insurance company
- **Confidence scoring** — Quantified approval prediction with actionable feedback
- **Human-in-the-loop** — Automatic routing when AI confidence is low
- **Full audit trail** — Every tool call logged for compliance and transparency
- **Authorization letter generation** — Ready-to-submit documents

## Project Structure

```
ClinicalPriorAuthAgent/
├── main.py              # FastAPI backend + agent orchestration
├── payer_policies.py    # Payer policy database + sample cases
├── static/index.html    # React frontend dashboard
├── requirements.txt     # Python dependencies
└── .env                 # Azure OpenAI credentials (not committed)
```

## Team

Built by **Senay Yakut** at Musa Labs Hackathon SF 2026
