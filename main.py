"""
ClearPath — Clinical Prior Authorization Agent
Built with Azure OpenAI GPT-4.1 + FastAPI
Hackathon: Musa Labs SF — Enterprise Agents (Feb 27, 2026)
"""

import json
import os
import uuid
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import AzureOpenAI
from pydantic import BaseModel

from payer_policies import (
    CPT_DATABASE,
    ICD10_DATABASE,
    PAYER_POLICIES,
    SAMPLE_CASES,
)
from rag_engine import rag_engine

load_dotenv()

# --- Azure OpenAI Client ---
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-03-01-preview"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)
DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4.1")

# --- FastAPI App ---
app = FastAPI(title="ClearPath — Prior Authorization Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- In-memory case store ---
cases_db: dict = {}
review_queue: list = []

# --- Pydantic Models ---
class CaseSubmission(BaseModel):
    patient_name: str
    patient_age: int
    patient_gender: str
    insurance_payer: str
    member_id: str
    referring_physician: str
    physician_npi: str
    procedure_requested: str
    cpt_codes: list[str]
    icd10_codes: list[str]
    clinical_notes: str

class ReviewDecision(BaseModel):
    case_id: str
    decision: str  # "approved" or "denied"
    reviewer_notes: str = ""

# --- Agent Tool Definitions (OpenAI function calling) ---
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "extract_diagnosis",
            "description": "Extract and validate ICD-10 diagnosis codes and CPT procedure codes from clinical notes. Returns structured diagnostic information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "icd10_codes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "ICD-10 diagnosis codes"
                    },
                    "cpt_codes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "CPT procedure codes"
                    },
                    "primary_diagnosis": {
                        "type": "string",
                        "description": "Primary diagnosis description"
                    },
                    "clinical_summary": {
                        "type": "string",
                        "description": "Brief clinical summary from notes"
                    }
                },
                "required": ["icd10_codes", "cpt_codes", "primary_diagnosis", "clinical_summary"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_payer_policy",
            "description": "Look up payer-specific prior authorization requirements for the given procedure and insurance company.",
            "parameters": {
                "type": "object",
                "properties": {
                    "payer_id": {
                        "type": "string",
                        "description": "Insurance payer identifier (e.g., united_healthcare, aetna, blue_cross_blue_shield)"
                    },
                    "procedure_type": {
                        "type": "string",
                        "description": "Type of procedure (e.g., MRI, knee_replacement, cardiac_catheterization, biologics)"
                    }
                },
                "required": ["payer_id", "procedure_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "draft_auth_request",
            "description": "Draft a formal prior authorization request letter with clinical justification.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_name": {"type": "string"},
                    "member_id": {"type": "string"},
                    "payer_name": {"type": "string"},
                    "procedure": {"type": "string"},
                    "cpt_codes": {"type": "array", "items": {"type": "string"}},
                    "icd10_codes": {"type": "array", "items": {"type": "string"}},
                    "clinical_justification": {"type": "string", "description": "Detailed clinical justification for the procedure"},
                    "referring_physician": {"type": "string"},
                    "physician_npi": {"type": "string"},
                    "supporting_documentation": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of supporting documents included"
                    }
                },
                "required": ["patient_name", "member_id", "payer_name", "procedure", "cpt_codes", "icd10_codes", "clinical_justification", "referring_physician", "physician_npi"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "predict_approval",
            "description": "Predict the likelihood of prior authorization approval based on clinical evidence and payer requirements.",
            "parameters": {
                "type": "object",
                "properties": {
                    "confidence_score": {
                        "type": "number",
                        "description": "Confidence score 0-100 for approval likelihood"
                    },
                    "risk_level": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Risk level for denial"
                    },
                    "strengths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Factors supporting approval"
                    },
                    "weaknesses": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Factors that may lead to denial"
                    },
                    "missing_documentation": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Documentation that should be added to strengthen the request"
                    },
                    "recommendation": {
                        "type": "string",
                        "description": "Final recommendation: submit, revise, or escalate"
                    }
                },
                "required": ["confidence_score", "risk_level", "strengths", "weaknesses", "missing_documentation", "recommendation"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "route_to_human",
            "description": "Route the case to a human reviewer when confidence is low or the case requires clinical judgment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Reason for human review"
                    },
                    "urgency": {
                        "type": "string",
                        "enum": ["routine", "urgent", "stat"],
                        "description": "Urgency level"
                    },
                    "suggested_reviewer": {
                        "type": "string",
                        "description": "Suggested type of reviewer (e.g., clinical nurse, medical director)"
                    },
                    "key_questions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Key questions for the reviewer to address"
                    }
                },
                "required": ["reason", "urgency", "suggested_reviewer", "key_questions"]
            }
        }
    }
]

# --- Tool Execution Functions ---
def execute_extract_diagnosis(args: dict) -> dict:
    """Validate and enrich diagnosis codes."""
    enriched_icd10 = []
    for code in args.get("icd10_codes", []):
        info = ICD10_DATABASE.get(code, {"description": "Unknown code", "category": "unknown"})
        enriched_icd10.append({"code": code, **info})

    enriched_cpt = []
    for code in args.get("cpt_codes", []):
        desc = CPT_DATABASE.get(code, "Unknown procedure")
        enriched_cpt.append({"code": code, "description": desc})

    return {
        "status": "success",
        "diagnoses": enriched_icd10,
        "procedures": enriched_cpt,
        "primary_diagnosis": args.get("primary_diagnosis", ""),
        "clinical_summary": args.get("clinical_summary", ""),
    }


def execute_lookup_payer_policy(args: dict) -> dict:
    """Look up payer policy requirements using RAG vector search."""
    payer_id = args.get("payer_id", "").lower().replace(" ", "_")
    procedure_type = args.get("procedure_type", "").lower().replace(" ", "_")

    # --- RAG: Semantic search over policy documents ---
    query = f"{procedure_type} prior authorization requirements {payer_id.replace('_', ' ')}"
    rag_results = rag_engine.search(query, top_k=2, payer_filter=payer_id)

    # Also get structured data from policy database as supplement
    payer = PAYER_POLICIES.get(payer_id)
    structured_policy = None
    if payer:
        structured_policy = payer["policies"].get(procedure_type)

    if not rag_results and not structured_policy:
        return {
            "status": "not_found",
            "message": f"No policy found for '{procedure_type}' under payer '{payer_id}'.",
        }

    response = {
        "status": "success",
        "payer_id": payer_id,
        "procedure_type": procedure_type,
        "retrieval_method": "RAG_vector_search",
        "rag_results": [
            {
                "document_id": r["document_id"],
                "title": r["title"],
                "similarity_score": r["similarity_score"],
                "content": r["content"],
            }
            for r in rag_results
        ],
    }

    # Merge structured policy data if available
    if structured_policy:
        response["structured_policy"] = {
            "payer_name": payer["name"] if payer else payer_id,
            "requires_prior_auth": structured_policy.get("requires_prior_auth"),
            "required_documentation": structured_policy.get("required_documentation", []),
            "auto_approve_criteria": structured_policy.get("auto_approve_criteria", []),
            "typical_turnaround": structured_policy.get("typical_turnaround"),
            "appeal_window": structured_policy.get("appeal_window"),
        }

    return response


def execute_draft_auth_request(args: dict) -> dict:
    """Generate the authorization request document."""
    today = datetime.now().strftime("%B %d, %Y")

    cpt_descriptions = [f"{c} — {CPT_DATABASE.get(c, 'Unknown')}" for c in args.get("cpt_codes", [])]
    icd_descriptions = []
    for code in args.get("icd10_codes", []):
        info = ICD10_DATABASE.get(code, {"description": "Unknown"})
        desc = info if isinstance(info, str) else info.get("description", "Unknown")
        icd_descriptions.append(f"{code} — {desc}")

    letter = f"""
PRIOR AUTHORIZATION REQUEST
Date: {today}
{'='*60}

TO: {args.get('payer_name', 'Insurance Company')}
    Prior Authorization Department

FROM: {args.get('referring_physician', 'Physician')}
      NPI: {args.get('physician_npi', 'N/A')}

RE: Prior Authorization Request for {args.get('procedure', 'Procedure')}

PATIENT INFORMATION:
  Name: {args.get('patient_name', 'Patient')}
  Member ID: {args.get('member_id', 'N/A')}

PROCEDURE REQUESTED:
  {args.get('procedure', 'N/A')}
  CPT Code(s): {', '.join(cpt_descriptions)}

DIAGNOSIS:
  {chr(10).join(f'  {d}' for d in icd_descriptions)}

CLINICAL JUSTIFICATION:
{args.get('clinical_justification', 'N/A')}

SUPPORTING DOCUMENTATION INCLUDED:
{chr(10).join(f'  - {doc}' for doc in args.get('supporting_documentation', ['Clinical notes', 'Imaging results']))}

I certify that the above information is accurate and that this procedure
is medically necessary for the care of this patient.

Respectfully,
{args.get('referring_physician', 'Physician')}
{'='*60}
    """.strip()

    return {
        "status": "success",
        "auth_request_letter": letter,
        "generated_at": today,
    }


def execute_predict_approval(args: dict) -> dict:
    """Return the prediction results."""
    return {
        "status": "success",
        "confidence_score": args.get("confidence_score", 50),
        "risk_level": args.get("risk_level", "medium"),
        "strengths": args.get("strengths", []),
        "weaknesses": args.get("weaknesses", []),
        "missing_documentation": args.get("missing_documentation", []),
        "recommendation": args.get("recommendation", "revise"),
        "requires_human_review": args.get("confidence_score", 50) < 70,
    }


def execute_route_to_human(args: dict) -> dict:
    """Flag the case for human review."""
    return {
        "status": "routed",
        "reason": args.get("reason", ""),
        "urgency": args.get("urgency", "routine"),
        "suggested_reviewer": args.get("suggested_reviewer", "clinical nurse"),
        "key_questions": args.get("key_questions", []),
        "message": "Case has been flagged for human review.",
    }


TOOL_EXECUTORS = {
    "extract_diagnosis": execute_extract_diagnosis,
    "lookup_payer_policy": execute_lookup_payer_policy,
    "draft_auth_request": execute_draft_auth_request,
    "predict_approval": execute_predict_approval,
    "route_to_human": execute_route_to_human,
}


# --- Agent Orchestration ---
def run_agent(case: dict) -> dict:
    """Run the Prior Auth agent loop with Azure OpenAI GPT-4.1."""

    system_prompt = """You are ClearPath, a clinical prior authorization specialist AI agent.
Your job is to process patient cases and prepare prior authorization requests for insurance companies.

For each case, you MUST call these tools IN ORDER:
1. extract_diagnosis — Extract and validate ICD-10 and CPT codes from the clinical notes
2. lookup_payer_policy — Look up the specific payer's requirements for this procedure
3. draft_auth_request — Draft the formal authorization request letter
4. predict_approval — Predict approval likelihood and identify gaps
5. route_to_human — If confidence < 70%, route to human reviewer

Be thorough, accurate, and always prioritize patient care.
Use clinical evidence from the notes to build the strongest possible case.
Flag any missing documentation that could strengthen the request.

IMPORTANT: You must call each tool with complete, well-structured arguments.
For the procedure type in lookup_payer_policy, map the procedure to one of: MRI, knee_replacement, cardiac_catheterization, biologics.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"""Process this prior authorization case:

Patient: {case['patient_name']}, {case['patient_age']}yo {case['patient_gender']}
Insurance: {case['insurance_payer']} (Member ID: {case['member_id']})
Referring Physician: {case['referring_physician']} (NPI: {case['physician_npi']})
Procedure: {case['procedure_requested']}
CPT Codes: {', '.join(case['cpt_codes'])}
ICD-10 Codes: {', '.join(case['icd10_codes'])}

Clinical Notes:
{case['clinical_notes']}

Please process this case by calling all required tools in sequence."""}
    ]

    tool_results = []
    max_iterations = 10

    for _ in range(max_iterations):
        response = client.chat.completions.create(
            model=DEPLOYMENT,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.1,
        )

        choice = response.choices[0]

        if choice.finish_reason == "stop":
            # Agent is done — collect final summary
            final_summary = choice.message.content or ""
            return {
                "status": "completed",
                "tool_results": tool_results,
                "agent_summary": final_summary,
            }

        if choice.message.tool_calls:
            messages.append(choice.message)

            for tool_call in choice.message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)

                executor = TOOL_EXECUTORS.get(fn_name)
                if executor:
                    result = executor(fn_args)
                    tool_results.append({
                        "tool": fn_name,
                        "input": fn_args,
                        "output": result,
                    })
                else:
                    result = {"error": f"Unknown tool: {fn_name}"}

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                })
        else:
            # No tool calls, no stop — just content
            if choice.message.content:
                return {
                    "status": "completed",
                    "tool_results": tool_results,
                    "agent_summary": choice.message.content,
                }
            break

    return {
        "status": "completed",
        "tool_results": tool_results,
        "agent_summary": "Agent completed processing.",
    }


# --- Startup: Initialize RAG Engine ---
@app.on_event("startup")
async def startup_event():
    try:
        rag_engine.initialize()
        print("RAG Engine initialized with vector embeddings.")
    except Exception as e:
        print(f"RAG Engine: Falling back to keyword search. Error: {e}")


# --- API Endpoints ---
@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")


@app.get("/api/sample-cases")
async def get_sample_cases():
    return SAMPLE_CASES


@app.post("/api/cases")
async def submit_case(case: CaseSubmission):
    case_id = f"PA-{uuid.uuid4().hex[:8].upper()}"
    case_data = {
        "case_id": case_id,
        "submitted_at": datetime.now().isoformat(),
        "status": "processing",
        **case.model_dump(),
    }
    cases_db[case_id] = case_data

    # Run the agent
    try:
        agent_result = run_agent(case.model_dump())
    except Exception as e:
        cases_db[case_id]["status"] = "error"
        cases_db[case_id]["error"] = str(e)
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    # Extract key results
    confidence = 50
    requires_review = False
    auth_letter = ""

    for tr in agent_result.get("tool_results", []):
        if tr["tool"] == "predict_approval":
            confidence = tr["output"].get("confidence_score", 50)
            requires_review = tr["output"].get("requires_human_review", False)
        if tr["tool"] == "draft_auth_request":
            auth_letter = tr["output"].get("auth_request_letter", "")

    status = "pending_review" if requires_review else "auto_approved" if confidence >= 85 else "ready_to_submit"

    cases_db[case_id].update({
        "status": status,
        "agent_result": agent_result,
        "confidence_score": confidence,
        "requires_human_review": requires_review,
        "auth_letter": auth_letter,
    })

    if requires_review:
        review_queue.append(case_id)

    return cases_db[case_id]


@app.get("/api/cases")
async def list_cases():
    return list(cases_db.values())


@app.get("/api/cases/{case_id}")
async def get_case(case_id: str):
    if case_id not in cases_db:
        raise HTTPException(status_code=404, detail="Case not found")
    return cases_db[case_id]


@app.get("/api/review-queue")
async def get_review_queue():
    return [cases_db[cid] for cid in review_queue if cid in cases_db]


@app.post("/api/review")
async def submit_review(decision: ReviewDecision):
    if decision.case_id not in cases_db:
        raise HTTPException(status_code=404, detail="Case not found")

    cases_db[decision.case_id].update({
        "status": decision.decision,
        "reviewer_notes": decision.reviewer_notes,
        "reviewed_at": datetime.now().isoformat(),
    })

    if decision.case_id in review_queue:
        review_queue.remove(decision.case_id)

    return cases_db[decision.case_id]


@app.get("/api/rag-search")
async def rag_search(query: str, payer: str = None, top_k: int = 3):
    """Direct RAG search endpoint — useful for demo."""
    results = rag_engine.search(query, top_k=top_k, payer_filter=payer)
    return {
        "query": query,
        "payer_filter": payer,
        "results": results,
        "retrieval_method": "vector_search" if rag_engine._initialized else "keyword_fallback",
    }


@app.get("/api/stats")
async def get_stats():
    total = len(cases_db)
    statuses = {}
    for c in cases_db.values():
        s = c.get("status", "unknown")
        statuses[s] = statuses.get(s, 0) + 1

    avg_confidence = 0
    confidence_cases = [c for c in cases_db.values() if "confidence_score" in c]
    if confidence_cases:
        avg_confidence = sum(c["confidence_score"] for c in confidence_cases) / len(confidence_cases)

    return {
        "total_cases": total,
        "statuses": statuses,
        "pending_reviews": len(review_queue),
        "average_confidence": round(avg_confidence, 1),
    }


if __name__ == "__main__":
    import uvicorn
    os.makedirs("static", exist_ok=True)
    uvicorn.run(app, host="0.0.0.0", port=8080)
