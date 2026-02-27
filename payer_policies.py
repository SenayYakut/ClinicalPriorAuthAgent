"""
Mock payer policy database for Prior Authorization requirements.
In production, this would be Azure AI Search over real policy documents.
"""

PAYER_POLICIES = {
    "united_healthcare": {
        "name": "United Healthcare",
        "policies": {
            "MRI": {
                "cpt_codes": ["70553", "70551", "70552", "72141", "72148", "73721"],
                "requires_prior_auth": True,
                "required_documentation": [
                    "Clinical indication/diagnosis",
                    "Previous conservative treatment history (minimum 6 weeks)",
                    "Physical examination findings",
                    "Previous imaging results if applicable",
                    "Referring physician NPI"
                ],
                "auto_approve_criteria": [
                    "Post-surgical follow-up within 6 months",
                    "Known malignancy staging/restaging",
                    "Acute neurological deficit"
                ],
                "typical_turnaround": "2-3 business days",
                "appeal_window": "180 days"
            },
            "knee_replacement": {
                "cpt_codes": ["27447", "27446"],
                "requires_prior_auth": True,
                "required_documentation": [
                    "X-ray showing bone-on-bone arthritis (Kellgren-Lawrence Grade III-IV)",
                    "BMI documentation (BMI < 40 preferred)",
                    "Conservative treatment failure (PT, NSAIDs, injections) for 3+ months",
                    "Functional assessment score (KOOS or similar)",
                    "Medical clearance for surgery",
                    "Orthopedic surgeon evaluation notes"
                ],
                "auto_approve_criteria": [
                    "Failed 3+ months conservative treatment with documented functional decline",
                    "Kellgren-Lawrence Grade IV with severe functional limitation"
                ],
                "typical_turnaround": "5-7 business days",
                "appeal_window": "180 days"
            },
            "cardiac_catheterization": {
                "cpt_codes": ["93458", "93459", "93460", "93461"],
                "requires_prior_auth": True,
                "required_documentation": [
                    "Positive stress test or abnormal imaging",
                    "Cardiac risk factor assessment",
                    "EKG results",
                    "Prior cardiac history",
                    "Cardiology consultation notes"
                ],
                "auto_approve_criteria": [
                    "STEMI or NSTEMI presentation",
                    "Unstable angina with positive troponin",
                    "Acute coronary syndrome"
                ],
                "typical_turnaround": "1-2 business days (urgent), 3-5 business days (routine)",
                "appeal_window": "180 days"
            },
            "biologics": {
                "cpt_codes": ["J0135", "J0717", "J1745", "J2182", "J3590"],
                "requires_prior_auth": True,
                "required_documentation": [
                    "Confirmed diagnosis with supporting labs/imaging",
                    "Trial and failure of conventional therapies",
                    "Disease activity score (DAS28, CDAI, or equivalent)",
                    "TB screening results",
                    "Hepatitis B/C screening",
                    "Vaccination status"
                ],
                "auto_approve_criteria": [
                    "Step therapy completion documented",
                    "Continuation of previously approved biologic with documented efficacy"
                ],
                "typical_turnaround": "5-10 business days",
                "appeal_window": "180 days"
            }
        }
    },
    "aetna": {
        "name": "Aetna",
        "policies": {
            "MRI": {
                "cpt_codes": ["70553", "70551", "70552", "72141", "72148", "73721"],
                "requires_prior_auth": True,
                "required_documentation": [
                    "Clinical indication with ICD-10 code",
                    "Conservative treatment attempted (4+ weeks)",
                    "Physical exam findings",
                    "Prior imaging if available"
                ],
                "auto_approve_criteria": [
                    "Emergency/trauma",
                    "Cancer staging",
                    "Pre-surgical planning for approved procedure"
                ],
                "typical_turnaround": "2 business days",
                "appeal_window": "365 days"
            },
            "knee_replacement": {
                "cpt_codes": ["27447", "27446"],
                "requires_prior_auth": True,
                "required_documentation": [
                    "Weight-bearing X-rays within 6 months",
                    "BMI < 40 (or documented exception)",
                    "Physical therapy completion (6+ weeks)",
                    "Failed pharmacological management",
                    "Surgical evaluation with operative plan"
                ],
                "auto_approve_criteria": [
                    "Grade IV OA with failed 6+ months conservative treatment"
                ],
                "typical_turnaround": "5 business days",
                "appeal_window": "365 days"
            },
            "cardiac_catheterization": {
                "cpt_codes": ["93458", "93459", "93460", "93461"],
                "requires_prior_auth": False,
                "required_documentation": [],
                "auto_approve_criteria": [],
                "typical_turnaround": "N/A - no prior auth required",
                "appeal_window": "N/A"
            },
            "biologics": {
                "cpt_codes": ["J0135", "J0717", "J1745", "J2182"],
                "requires_prior_auth": True,
                "required_documentation": [
                    "Diagnosis confirmation with labs",
                    "Step therapy documentation (2+ conventional DMARDs)",
                    "Disease activity assessment",
                    "Infection screening (TB, Hep B/C)"
                ],
                "auto_approve_criteria": [
                    "Documented failure of 2+ conventional therapies",
                    "Reauthorization with documented response"
                ],
                "typical_turnaround": "3-5 business days",
                "appeal_window": "365 days"
            }
        }
    },
    "blue_cross_blue_shield": {
        "name": "Blue Cross Blue Shield",
        "policies": {
            "MRI": {
                "cpt_codes": ["70553", "70551", "70552", "72141", "72148"],
                "requires_prior_auth": True,
                "required_documentation": [
                    "Order from treating physician with clinical rationale",
                    "Duration and nature of symptoms",
                    "Conservative treatment history",
                    "Relevant physical exam findings"
                ],
                "auto_approve_criteria": [
                    "Red flag symptoms (progressive neurological deficit, suspected cauda equina)",
                    "Cancer surveillance per NCCN guidelines",
                    "Post-operative evaluation"
                ],
                "typical_turnaround": "2-3 business days",
                "appeal_window": "180 days"
            },
            "knee_replacement": {
                "cpt_codes": ["27447", "27446"],
                "requires_prior_auth": True,
                "required_documentation": [
                    "Radiographic evidence of severe arthritis",
                    "Documented failure of non-surgical management (3+ months)",
                    "Functional limitation documentation",
                    "Medical necessity letter from orthopedic surgeon",
                    "Pre-operative medical clearance"
                ],
                "auto_approve_criteria": [
                    "Revision of previously approved arthroplasty",
                    "Fracture requiring arthroplasty"
                ],
                "typical_turnaround": "3-5 business days",
                "appeal_window": "180 days"
            }
        }
    }
}

# Common ICD-10 code mappings for clinical context
ICD10_DATABASE = {
    "M17.11": {"description": "Primary osteoarthritis, right knee", "category": "knee"},
    "M17.12": {"description": "Primary osteoarthritis, left knee", "category": "knee"},
    "M17.0": {"description": "Bilateral primary osteoarthritis of knee", "category": "knee"},
    "M54.5": {"description": "Low back pain", "category": "spine"},
    "M54.2": {"description": "Cervicalgia", "category": "spine"},
    "G89.29": {"description": "Other chronic pain", "category": "pain"},
    "I25.10": {"description": "Atherosclerotic heart disease of native coronary artery", "category": "cardiac"},
    "I20.0": {"description": "Unstable angina", "category": "cardiac"},
    "I21.3": {"description": "ST elevation myocardial infarction of unspecified site", "category": "cardiac"},
    "M05.79": {"description": "Rheumatoid arthritis with rheumatoid factor, unspecified site", "category": "rheumatology"},
    "M06.9": {"description": "Rheumatoid arthritis, unspecified", "category": "rheumatology"},
    "K50.90": {"description": "Crohn's disease, unspecified, without complications", "category": "gastroenterology"},
    "L40.50": {"description": "Arthropathic psoriasis, unspecified", "category": "rheumatology"},
    "C34.90": {"description": "Malignant neoplasm of unspecified part of bronchus or lung", "category": "oncology"},
    "C50.919": {"description": "Malignant neoplasm of unspecified site of breast", "category": "oncology"},
    "G43.909": {"description": "Migraine, unspecified, not intractable", "category": "neurology"},
    "S83.511A": {"description": "Sprain of anterior cruciate ligament of right knee, initial encounter", "category": "knee"},
}

# CPT code descriptions
CPT_DATABASE = {
    "27447": "Total knee arthroplasty",
    "27446": "Partial knee arthroplasty (unicompartmental)",
    "70553": "MRI brain with and without contrast",
    "70551": "MRI brain without contrast",
    "70552": "MRI brain with contrast",
    "72141": "MRI cervical spine without contrast",
    "72148": "MRI lumbar spine without contrast",
    "73721": "MRI lower extremity joint without contrast",
    "93458": "Left heart catheterization",
    "93459": "Left heart catheterization with left ventriculography",
    "93460": "Right and left heart catheterization",
    "93461": "Right and left heart catheterization with ventriculography",
    "J0135": "Adalimumab injection (Humira)",
    "J0717": "Certolizumab pegol injection (Cimzia)",
    "J1745": "Infliximab injection (Remicade)",
    "J2182": "Mepolizumab injection (Nucala)",
    "J3590": "Unclassified biologic",
    "99213": "Office visit, established patient, low complexity",
    "99214": "Office visit, established patient, moderate complexity",
}

SAMPLE_CASES = [
    {
        "id": "CASE-001",
        "patient_name": "Maria Rodriguez",
        "patient_age": 67,
        "patient_gender": "Female",
        "insurance_payer": "united_healthcare",
        "member_id": "UHC-889234571",
        "referring_physician": "Dr. James Chen, MD",
        "physician_npi": "1234567890",
        "procedure_requested": "Total Knee Replacement",
        "cpt_codes": ["27447"],
        "icd10_codes": ["M17.11"],
        "clinical_notes": """
Patient is a 67-year-old female presenting with severe right knee pain and functional limitation
due to end-stage osteoarthritis. She has been symptomatic for 18 months with progressive worsening.

Conservative treatments attempted:
- Physical therapy: 12 weeks (completed March-June 2025), minimal improvement
- NSAIDs (Meloxicam 15mg daily): 6 months, partial relief only
- Corticosteroid injection (Kenalog 40mg): 2 injections (Jan 2025, July 2025), temporary relief lasting ~6 weeks each
- Hyaluronic acid injection (Synvisc): 1 series (Sept 2025), no significant improvement

Current functional status:
- Unable to walk more than 1 block without severe pain (VAS 8/10)
- Requires assistive device (cane) for ambulation
- Cannot climb stairs without significant difficulty
- Sleep disrupted nightly due to pain
- KOOS score: 34/100 (severe functional limitation)

Imaging: Weight-bearing AP/lateral X-rays (Dec 2025) show Kellgren-Lawrence Grade IV changes
with complete loss of medial joint space, subchondral sclerosis, and osteophyte formation.

BMI: 29.3 (overweight but within acceptable range)

Medical clearance obtained from primary care (Dr. Smith, Jan 2026).
Cardiac clearance obtained (Dr. Patel, Jan 2026).

Recommendation: Total knee arthroplasty, right knee. Patient has exhausted conservative options
and has significant functional limitation affecting quality of life.
        """,
    },
    {
        "id": "CASE-002",
        "patient_name": "James Thompson",
        "patient_age": 52,
        "patient_gender": "Male",
        "insurance_payer": "aetna",
        "member_id": "AET-445678123",
        "referring_physician": "Dr. Sarah Williams, MD",
        "physician_npi": "9876543210",
        "procedure_requested": "MRI Lumbar Spine",
        "cpt_codes": ["72148"],
        "icd10_codes": ["M54.5", "G89.29"],
        "clinical_notes": """
Patient is a 52-year-old male with chronic low back pain for 8 weeks, not improving with
conservative management. No red flag symptoms (no bowel/bladder dysfunction, no progressive
neurological deficit, no history of cancer, no unexplained weight loss).

Conservative treatments:
- NSAIDs (Ibuprofen 800mg TID): 4 weeks with minimal relief
- Physical therapy: Started 3 weeks ago, ongoing
- Muscle relaxant (Cyclobenzaprine): 2 weeks, some improvement in spasm

Physical exam:
- Tenderness over L4-L5 paraspinal muscles
- Negative straight leg raise bilaterally
- Full strength in lower extremities (5/5)
- Intact sensation
- Normal reflexes

No prior imaging of lumbar spine.

Requesting MRI lumbar spine to evaluate for disc pathology given persistent symptoms
despite 8 weeks of conservative treatment.
        """,
    },
    {
        "id": "CASE-003",
        "patient_name": "Robert Kim",
        "patient_age": 71,
        "patient_gender": "Male",
        "insurance_payer": "blue_cross_blue_shield",
        "member_id": "BCBS-771234890",
        "referring_physician": "Dr. Michael Patel, MD",
        "physician_npi": "5678901234",
        "procedure_requested": "MRI Brain",
        "cpt_codes": ["70553"],
        "icd10_codes": ["G43.909"],
        "clinical_notes": """
Patient is a 71-year-old male with new-onset severe headaches for 2 weeks, different from
his usual tension headaches. Patient describes sudden onset, worst headache of his life,
with associated photophobia and neck stiffness.

Concerning features:
- New headache pattern in patient >50 years old
- Sudden onset with maximum intensity at onset ("thunderclap" quality)
- Associated neck stiffness
- No prior history of migraines

Physical exam:
- BP 158/92
- Mild nuchal rigidity
- No papilledema on fundoscopic exam
- No focal neurological deficits
- GCS 15

CT Head (performed in ED): No acute intracranial hemorrhage. No mass lesion.

Requesting MRI Brain with and without contrast for further evaluation of new-onset
severe headache with concerning features in elderly patient. Need to rule out
cerebral venous thrombosis, vasculitis, or subtle mass lesion not visible on CT.
        """,
    },
]
