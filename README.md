# ClearPath — Clinical Prior Authorization Agent

> **Prior authorization costs US hospitals $13B/year in administrative overhead and delays patient care by an average of 14 days.** ClearPath is an AI agent that processes authorization requests in under 30 seconds — from diagnosis extraction to approval prediction — using Azure OpenAI GPT-4.1.

Built by **Senay Yakut** at **Musa Labs Hackathon SF — Enterprise Agents** (Feb 27, 2026)

---

## The Problem

Every time a doctor orders a procedure, insurance companies require **prior authorization** — a formal request proving medical necessity. Today this process is:

- **Slow**: 3–14 day average turnaround
- **Expensive**: $13B/year in US hospital admin costs
- **Error-prone**: 34% of requests initially denied due to incomplete documentation
- **Manual**: 45 minutes of staff time per request reading policy PDFs and filling forms

## What ClearPath Does

ClearPath is a **multi-step AI agent** that automates the entire prior authorization workflow:

```
Patient Case Input
       │
       ▼
┌──────────────────────────────────────────────────┐
│           Azure OpenAI GPT-4.1 Agent             │
│                                                  │
│  ┌─────────────────┐  ┌──────────────────────┐   │
│  │ 1. Extract       │  │ 2. Policy Lookup     │   │
│  │    Diagnosis     │  │    (RAG Search)       │   │
│  │    ICD-10 / CPT  │  │    8 policy docs      │   │
│  └────────┬────────┘  └──────────┬───────────┘   │
│           │                      │               │
│  ┌────────▼────────┐  ┌──────────▼───────────┐   │
│  │ 3. Draft Auth   │  │ 4. Predict Approval  │   │
│  │    Request      │  │    Confidence Score   │   │
│  │    Letter       │  │    Gap Analysis       │   │
│  └────────┬────────┘  └──────────┬───────────┘   │
│           │                      │               │
│           └──────────┬───────────┘               │
│                      │                           │
│           ┌──────────▼───────────┐               │
│           │ 5. Route Decision    │               │
│           │    ≥70% → Submit     │               │
│           │    <70% → Human HITL │               │
│           └──────────────────────┘               │
└──────────────────────────────────────────────────┘
       │
       ▼
Output: Auth letter + confidence score + audit trail
```

## Key Features

| Feature | Description |
|---------|-------------|
| **Multi-step Agent** | 5 tools called sequentially with full context passing via GPT-4.1 function calling |
| **RAG Pipeline** | TF-IDF vector search over 8 payer policy documents across 3 insurance companies (UHC, Aetna, BCBS) |
| **Confidence Scoring** | Quantified approval prediction with strengths, risks, and missing documentation analysis |
| **Human-in-the-Loop** | Automatic routing to clinical reviewers when confidence < 70% — no autonomous decisions on borderline cases |
| **Authorization Letters** | Auto-generated formal request letters with clinical justification mapped to payer requirements |
| **Full Audit Trail** | Every tool call logged with inputs and outputs for HIPAA compliance and transparency |

## Sample Cases

The app ships with 5 cases spanning the full approval spectrum:

| Patient | Procedure | Payer | Expected | Why |
|---------|-----------|-------|----------|-----|
| Maria Rodriguez, 67F | Total Knee Replacement | United Healthcare | **Approved ~90%** | Complete documentation, Grade IV OA, 18 months conservative treatment |
| Robert Kim, 71M | MRI Brain | Blue Cross Blue Shield | **Approved ~85%** | Red flag symptoms, elderly patient, CT completed |
| James Thompson, 52M | MRI Lumbar Spine | Aetna | **Borderline ~65%** | Only 8 weeks conservative treatment, no neurological findings |
| David Park, 43M | Total Knee Replacement | United Healthcare | **Denied ~25%** | Grade II only, BMI 46, no PT/injections/clearance |
| Susan Chen, 38F | Humira (Adalimumab) | Aetna | **Denied ~20%** | No DMARDs tried, no TB/Hep screening, no disease activity score |

## Tech Stack

| Component | Technology | Role |
|-----------|-----------|------|
| AI Engine | **Azure OpenAI GPT-4.1** | Multi-step clinical reasoning with function calling |
| Backend | **FastAPI** (Python) | API server + agent orchestration loop |
| RAG | **TF-IDF + Cosine Similarity** | Vector search over payer policy documents |
| Frontend | **React** (CDN) | Clinical dashboard with case submission + review |
| Policies | **8 documents, 3 payers** | UHC, Aetna, BCBS across 4 procedure categories |

**Production upgrade path**: Azure AI Search (replace TF-IDF), Cosmos DB (persistence), Azure Key Vault (PHI encryption), Azure Functions (serverless scaling).

## Quick Start

```bash
# Clone the repo
git clone https://github.com/SenayYakut/ClinicalPriorAuthAgent.git
cd ClinicalPriorAuthAgent

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Azure OpenAI credentials

# Run
python main.py
```

Open **http://localhost:8080** in your browser.

## Demo Flow

1. Open `http://localhost:8080`
2. Click a **sample case** — try "Maria Rodriguez" (strong) or "David Park" (weak)
3. Click **Submit for Prior Authorization**
4. Watch the agent process in ~10-30 seconds
5. Review: **confidence score**, **auth letter**, **agent trace**, **gap analysis**
6. Weak cases route to the **Review Queue** tab for human approval/denial

## Project Structure

```
ClinicalPriorAuthAgent/
├── main.py              # FastAPI backend + GPT-4.1 agent loop + API endpoints
├── rag_engine.py        # TF-IDF RAG pipeline over payer policy documents
├── payer_policies.py    # Policy database, ICD-10/CPT codes, 5 sample cases
├── static/index.html    # React frontend dashboard
├── presentation.html    # Hackathon presentation slides (arrow keys to navigate)
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
└── .gitignore           # Excludes .env, __pycache__, venv
```

## Responsible AI

- **Human-in-the-loop**: Agent never auto-approves uncertain cases (< 70% confidence)
- **Grounded retrieval**: RAG ensures agent references actual policy documents, not hallucinated requirements
- **Transparency**: Full tool execution trace visible for every case
- **Gap analysis**: Proactively flags missing documentation before submission
- **Audit compliance**: All inputs, outputs, and decisions logged for regulatory review

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Frontend dashboard |
| `GET` | `/api/sample-cases` | List sample cases |
| `POST` | `/api/cases` | Submit a case for processing |
| `GET` | `/api/cases` | List all processed cases |
| `GET` | `/api/cases/{id}` | Get case details |
| `GET` | `/api/review-queue` | Cases pending human review |
| `POST` | `/api/review` | Submit human review decision |
| `GET` | `/api/rag-search?query=...` | Direct RAG search over policies |
| `GET` | `/api/stats` | Dashboard statistics |

---

Built with Azure OpenAI GPT-4.1 at Musa Labs Hackathon SF 2026
