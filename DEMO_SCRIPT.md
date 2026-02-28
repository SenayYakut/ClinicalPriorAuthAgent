# ClearPath — Demo Script & Talking Points

## The Problem (60 seconds)

Prior authorization — getting insurance approval before a medical procedure — is one of the most broken workflows in US healthcare.

What happens today: A doctor orders a knee replacement. Staff must manually look up the insurance company's policy requirements buried in 100+ page PDFs, write clinical justification letters, gather supporting documents, and submit through fax or portal. Then wait days. 34% get denied on the first try — usually because of missing documentation — and the whole process starts over.

| Metric | Reality |
|--------|---------|
| **$13 billion/year** | Admin cost to US hospitals for prior auth |
| **14 days** | Average turnaround time per request |
| **45 minutes** | Staff time spent on a single request |
| **34%** | Initial denial rate due to incomplete submissions |
| **16 hours/week** | Time physicians spend on paperwork instead of patient care |

**Who it hurts:**
- Patients wait weeks for procedures they need
- Doctors burn hours on admin instead of care
- Hospitals spend millions on staff doing repetitive manual work

---

## The Solution (60 seconds)

ClearPath is an AI agent that automates the entire prior authorization workflow in 30 seconds.

**5-step agent pipeline:**

1. **Extract Diagnosis** — Validates ICD-10 and CPT codes from clinical notes
2. **Policy Lookup (RAG)** — Vector search retrieves the exact payer requirements from actual policy documents
3. **Draft Authorization Letter** — Generates a formal request with clinical justification mapped to payer requirements
4. **Predict Approval** — Confidence score with strengths, risks, and missing documentation
5. **Route Decision** — If confidence < 70%, routes to human reviewer (responsible AI)

**What makes this different from a chatbot:**
- It's a workflow agent, not a conversation
- It retrieves policy requirements via RAG — not hallucinated
- It has guardrails and human-in-the-loop
- It produces real output — a letter ready to submit

---

## Live Demo (90 seconds)

### Demo 1: Strong Case (Maria Rodriguez)
- Click "Maria Rodriguez" sample case — 67F, Total Knee Replacement, United Healthcare
- Submit → watch agent process
- **Show:** ~90% confidence, green approval, full auth letter, agent trace with all 5 steps
- **Say:** "This patient has Grade IV osteoarthritis, failed 18 months of conservative treatment, has medical clearance — the agent recognizes this meets all United Healthcare requirements and auto-approves."

### Demo 2: Weak Case (David Park)
- Click "David Park" — 43M, Total Knee Replacement, same insurer
- Submit → watch agent process
- **Show:** ~25% confidence, red denial, routed to Review Queue, missing documentation flagged
- **Say:** "Same procedure, same insurer, but this patient has Grade II arthritis, BMI of 46, no physical therapy, no injections, no medical clearance. The agent identifies 6 gaps, scores it at 25%, and routes it to a human reviewer instead of submitting a request that would be denied."

### Demo 3: Human-in-the-Loop
- Switch to Review Queue tab
- Show the denial case waiting for human review with reason, urgency, and key questions
- Click Approve or Deny
- **Say:** "The agent never makes autonomous decisions on borderline cases. This is responsible AI — the human stays in the loop."

---

## Enterprise Value (30 seconds)

**Would a hospital pay for this? Yes.**

- A mid-size hospital processes 5,000-10,000 prior auth requests per year
- At 45 min each, that's 3,750-7,500 hours of admin work
- Direct savings: **$130K-$260K per year per hospital**
- 300M+ prior auth requests processed annually in the US
- Existing solutions are portal-based form fillers — ClearPath is a reasoning agent

---

## Technical Depth (30 seconds — if judges ask)

- **Azure OpenAI GPT-4.1** with function calling — 5 tools orchestrated sequentially
- **RAG pipeline** — TF-IDF vector search over 8 payer policy documents, cosine similarity retrieval
- **3 payers, 4 procedure categories** — different requirements per insurer
- **Full audit trail** — every tool call logged with inputs and outputs
- **Production path:** Azure AI Search for embeddings, Cosmos DB for persistence, Azure Key Vault for PHI encryption

---

## 30-Second Pitch

> "Prior auth costs hospitals $13 billion a year. Staff spend 45 minutes per request reading policy PDFs and still get denied 34% of the time. ClearPath processes the entire workflow in 30 seconds — extracts diagnoses, retrieves payer-specific requirements through RAG, drafts the authorization letter, predicts approval likelihood, and routes borderline cases to a human reviewer. A mid-size hospital saves $250K per year and patients get to care faster."
