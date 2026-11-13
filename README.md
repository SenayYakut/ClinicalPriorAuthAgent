# ClearPath — Clinical Prior Authorization Agent

Prior authorization is one of the biggest administrative burdens in US healthcare, and it delays patient care by days or weeks. <!-- TODO: add a sourced stat here, or keep this sentence as is --> **ClearPath is an AI agent that processes an authorization request in under 30 seconds**, from diagnosis extraction to approval prediction, and **routes uncertain cases to a human reviewer** instead of acting on them.

Built by Senay Yakut at Musa Labs Hackathon SF — Enterprise Agents (Feb 27, 2026), using Azure OpenAI GPT-4.1.

---

## 🛡️ Oversight & Safety

Prior authorization is a high-stakes workflow: a wrong call can delay a patient's care. ClearPath is designed so the agent **flags its own uncertainty, hands borderline cases to a human, and leaves a trace a reviewer can follow**. The goal is to make failures *visible* instead of silent.

| Safeguard | How it works in ClearPath |
|---|---|
| **Confidence-gated routing** | Step 4 predicts an approval confidence score; cases **≥ 70%** proceed to submission, cases **< 70%** go to a human review queue |
| **Human-in-the-loop** | Borderline and weak cases appear in the **Review Queue**, where a clinical reviewer approves or denies (`GET /api/review-queue`, `POST /api/review`) |
| **Grounded retrieval** | Policy requirements come from RAG over 8 payer policy documents (UHC, Aetna, BCBS), not from the model's memory |
| **Gap analysis** | Before submission, the agent lists strengths, risks, and **missing documentation** so a reviewer sees *why* a case is weak |
| **Full audit trail** | Every tool call is logged with its inputs and outputs, and the full agent trace is visible in the UI for each case |

The agent never auto-submits a case it scores below the threshold.

### Known limitations (and what I'm working on)

- **The confidence score is the model's own estimate.** It's produced by GPT-4.1 as part of its reasoning and **has not been calibrated** against real outcomes. A confident-but-wrong prediction could still pass the 70% gate. *This is the open question I'm most interested in.*
- **Small, synthetic test set.** 5 hand-built cases and 8 policy documents; no real patient data, live EHR, or payer integration.
- **Simple retrieval.** TF-IDF can miss policy passages that use different wording than the case.
- **The audit trail is kept in memory for the demo**, not persisted or access-controlled; this is not a HIPAA-compliant system. <!-- TODO: confirm in main.py whether cases persist anywhere; edit if so -->

**In progress: evaluation harness** to measure:
- **Calibration:** are 90%-confidence predictions actually right more often than 70% ones?
- **Escalation quality:** does the 70% gate send the *right* cases to humans, and how many confident errors slip through?
- **Failure modes:** missing documentation, retrieval misses, and conflicting policy criteria.

---

## The Problem

Every time a doctor orders certain procedures, the insurer requires prior authorization: a formal request proving medical necessity. Today this process is:

- **Slow:** typically days to weeks of turnaround
- **Error-prone:** many requests are initially denied because documentation is incomplete
- **Manual:** staff spend a long time per request reading policy PDFs and filling out forms

<!-- TODO: if you want the specific numbers back ($13B/yr, 34% initial denials, 45 min per request), add a source link for each -->

## What ClearPath Does

ClearPath is a multi-step AI agent that automates the prior authorization workflow:

```
Patient Case Input
       │
       ▼
┌──────────────────────────────────────────────────┐
│           Azure OpenAI GPT-4.1 Agent             │
│                                                  │
│  ┌─────────────────┐  ┌──────────────────────┐   │
│  │ 1. Extract      │  │ 2. Policy Lookup     │   │
│  │    Diagnosis    │  │    (RAG Search)      │   │
│  │    ICD-10 / CPT │  │    8 policy docs     │   │
│  └────────┬────────┘  └──────────┬───────────┘   │
│           │                      │               │
│  ┌────────▼────────┐  ┌──────────▼───────────┐   │
│  │ 3. Draft Auth   │  │ 4. Predict Approval  │   │
│  │    Request      │  │    Confidence Score  │   │
│  │    Letter       │  │    Gap Analysis      │   │
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
|---|---|
| Multi-step Agent | 5 tools called sequentially with full context passing via GPT-4.1 function calling |
| RAG Pipeline | TF-IDF vector search over 8 payer policy documents across 3 insurers (UHC, Aetna, BCBS) |
| Confidence Scoring | Approval prediction with strengths, risks, and missing-documentation analysis |
| Human-in-the-Loop | Automatic routing to clinical reviewers when confidence < 70%; no autonomous decisions on borderline cases |
| Authorization Letters | Auto-generated request letters with clinical justification mapped to payer requirements |
| Full Audit Trail | Every tool call logged with inputs and outputs for transparency and review |

## Sample Cases

The app ships with 5 synthetic cases spanning the full approval spectrum:

| Patient | Procedure | Payer | Expected | Why |
|---|---|---|---|---|
| Maria Rodriguez, 67F | Total Knee Replacement | United Healthcare | Approved ~90% | Complete documentation, Grade IV OA, 18 months conservative treatment |
| Robert Kim, 71M | MRI Brain | Blue Cross Blue Shield | Approved ~85% | Red-flag symptoms, elderly patient, CT completed |
| James Thompson, 52M | MRI Lumbar Spine | Aetna | Borderline ~65% | Only 8 weeks conservative treatment, no neurological findings |
| David Park, 43M | Total Knee Replacement | United Healthcare | Denied ~25% | Grade II only, BMI 46, no PT/injections/clearance |
| Susan Chen, 38F | Humira (Adalimumab) | Aetna | Denied ~20% | No DMARDs tried, no TB/Hep screening, no disease activity score |

*All patients are fictional.*

## Tech Stack

| Component | Technology | Role |
|---|---|---|
| AI Engine | Azure OpenAI GPT-4.1 | Multi-step clinical reasoning with function calling |
| Backend | FastAPI (Python) | API server + agent orchestration loop |
| RAG | TF-IDF + Cosine Similarity | Search over payer policy documents |
| Frontend | React (CDN) | Clinical dashboard with case submission + review |
| Policies | 8 documents, 3 payers | UHC, Aetna, BCBS across 4 procedure categories |

**Production upgrade path:** Azure AI Search (replace TF-IDF), Cosmos DB (persistence), Azure Key Vault (PHI encryption), Azure Functions (serverless scaling).

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

Open http://localhost:8080 in your browser.

## Demo Flow

1. Open http://localhost:8080
2. Click a sample case: try "Maria Rodriguez" (strong) or "David Park" (weak)
3. Click **Submit for Prior Authorization**
4. Watch the agent process in ~10–30 seconds
5. Review: confidence score, auth letter, agent trace, gap analysis
6. Weak cases route to the **Review Queue** tab for human approval/denial

## Project Structure

```
ClinicalPriorAuthAgent/
├── main.py              # FastAPI backend + GPT-4.1 agent loop + API endpoints
├── rag_engine.py        # TF-IDF RAG pipeline over payer policy documents
├── payer_policies.py    # Policy database, ICD-10/CPT codes, 5 sample cases
├── static/index.html    # React frontend dashboard
├── DEMO_SCRIPT.md       # Demo talking points
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
└── .gitignore           # Excludes .env, __pycache__, venv
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Frontend dashboard |
| GET | `/api/sample-cases` | List sample cases |
| POST | `/api/cases` | Submit a case for processing |
| GET | `/api/cases` | List all processed cases |
| GET | `/api/cases/{id}` | Get case details |
| GET | `/api/review-queue` | Cases pending human review |
| POST | `/api/review` | Submit human review decision |
| GET | `/api/rag-search?query=...` | Direct RAG search over policies |
| GET | `/api/stats` | Dashboard statistics |

---

Built with Azure OpenAI GPT-4.1 at Musa Labs Hackathon SF 2026.
