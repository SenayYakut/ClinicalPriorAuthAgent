"""
RAG Engine — Vector search over payer policy documents.
Uses TF-IDF vectorization with cosine similarity for semantic retrieval.

In production, this would use Azure AI Search with OpenAI embeddings.
For the hackathon, we use sklearn TF-IDF vectors + cosine similarity
to demonstrate the RAG retrieval pattern without requiring an embeddings deployment.
"""

import re
import math
import numpy as np
from collections import Counter


# --- Policy Documents (simulating PDFs/docs ingested into vector store) ---
POLICY_DOCUMENTS = [
    {
        "id": "UHC-KNEE-001",
        "payer": "United Healthcare",
        "payer_id": "united_healthcare",
        "category": "knee_replacement",
        "title": "United Healthcare Prior Authorization Policy: Total Knee Arthroplasty",
        "content": """
UNITED HEALTHCARE PRIOR AUTHORIZATION POLICY
Procedure: Total Knee Arthroplasty (CPT 27447, 27446)

MEDICAL NECESSITY CRITERIA:
Prior authorization is REQUIRED for all total and partial knee arthroplasty procedures.

REQUIRED DOCUMENTATION:
1. Radiographic evidence: Weight-bearing X-rays showing Kellgren-Lawrence Grade III or IV
   osteoarthritis with bone-on-bone changes, subchondral sclerosis, or osteophyte formation.
2. BMI Documentation: Patient BMI must be documented. BMI < 40 is preferred. Patients with
   BMI >= 40 require additional documentation of weight management attempts.
3. Conservative Treatment Failure: Documented failure of conservative management for a
   minimum of 3 months, including at least TWO of the following:
   - Physical therapy (minimum 6 weeks)
   - NSAIDs or analgesic medications
   - Corticosteroid injections
   - Hyaluronic acid injections
   - Activity modification
4. Functional Assessment: Validated outcome score such as KOOS, WOMAC, or Oxford Knee Score
   demonstrating significant functional limitation.
5. Medical Clearance: Pre-operative medical clearance from primary care physician.
6. Orthopedic Evaluation: Detailed surgical evaluation notes from board-certified orthopedic surgeon.

AUTO-APPROVAL CRITERIA:
- Kellgren-Lawrence Grade IV with documented failure of 3+ months conservative treatment
  AND functional assessment score in severe range
- Revision of previously approved arthroplasty within 10 years
- Fracture requiring arthroplasty (emergent)

TYPICAL TURNAROUND: 5-7 business days
APPEAL WINDOW: 180 days from denial date
PEER-TO-PEER REVIEW: Available upon request within 5 business days of denial

EXCLUSIONS:
- Arthroscopic debridement as alternative not yet attempted (for patients under 55)
- Lack of radiographic evidence
- BMI > 45 without documented bariatric consultation
        """,
    },
    {
        "id": "UHC-MRI-001",
        "payer": "United Healthcare",
        "payer_id": "united_healthcare",
        "category": "MRI",
        "title": "United Healthcare Prior Authorization Policy: MRI Studies",
        "content": """
UNITED HEALTHCARE PRIOR AUTHORIZATION POLICY
Procedure: Magnetic Resonance Imaging (MRI)
CPT Codes: 70551-70553 (Brain), 72141 (C-Spine), 72148 (L-Spine), 73721 (Lower Extremity)

MEDICAL NECESSITY CRITERIA:
Prior authorization is REQUIRED for all outpatient MRI studies.

REQUIRED DOCUMENTATION:
1. Clinical indication with specific ICD-10 diagnosis code
2. Previous conservative treatment history (minimum 6 weeks for musculoskeletal)
3. Physical examination findings supporting the need for advanced imaging
4. Previous imaging results (X-ray, CT) if applicable
5. Referring physician NPI number

AUTO-APPROVAL CRITERIA (no prior auth needed):
- Post-surgical follow-up within 6 months of approved procedure
- Known malignancy: staging or restaging per NCCN guidelines
- Acute neurological deficit (new onset weakness, sensory loss, bowel/bladder dysfunction)
- Emergency/trauma setting
- Pre-surgical planning for previously approved procedure

DOCUMENTATION FOR SPECIFIC INDICATIONS:
Lumbar Spine MRI:
- Duration of symptoms (minimum 6 weeks without red flags)
- Trial of conservative treatment (PT, NSAIDs, activity modification)
- Negative or inconclusive X-rays
- Specific neurological findings on exam

Brain MRI:
- New neurological symptoms or findings
- Headache: new onset, change in pattern, or red flag features
- Seizure evaluation
- Known CNS pathology follow-up

TYPICAL TURNAROUND: 2-3 business days
APPEAL WINDOW: 180 days
        """,
    },
    {
        "id": "UHC-CARDIAC-001",
        "payer": "United Healthcare",
        "payer_id": "united_healthcare",
        "category": "cardiac_catheterization",
        "title": "United Healthcare Prior Authorization Policy: Cardiac Catheterization",
        "content": """
UNITED HEALTHCARE PRIOR AUTHORIZATION POLICY
Procedure: Cardiac Catheterization
CPT Codes: 93458, 93459, 93460, 93461

MEDICAL NECESSITY CRITERIA:
Prior authorization is REQUIRED for elective cardiac catheterization.

REQUIRED DOCUMENTATION:
1. Positive or abnormal non-invasive cardiac testing:
   - Stress test (exercise or pharmacologic) showing ischemia
   - Cardiac CT showing significant coronary calcification or stenosis
   - Echocardiogram showing wall motion abnormalities
2. Cardiac risk factor assessment (hypertension, diabetes, smoking, family history, hyperlipidemia)
3. Recent EKG results (within 30 days)
4. Prior cardiac history documentation
5. Cardiology consultation notes from board-certified cardiologist

AUTO-APPROVAL (no prior auth):
- STEMI or NSTEMI presentation (emergent)
- Unstable angina with positive troponin
- Acute coronary syndrome
- Cardiogenic shock
- Cardiac arrest survivor

TYPICAL TURNAROUND: 1-2 business days (urgent), 3-5 business days (routine)
APPEAL WINDOW: 180 days
        """,
    },
    {
        "id": "UHC-BIOLOGICS-001",
        "payer": "United Healthcare",
        "payer_id": "united_healthcare",
        "category": "biologics",
        "title": "United Healthcare Prior Authorization Policy: Biologic Therapies",
        "content": """
UNITED HEALTHCARE PRIOR AUTHORIZATION POLICY
Procedure: Biologic and Biosimilar Therapies
CPT/HCPCS Codes: J0135 (Adalimumab/Humira), J0717 (Certolizumab/Cimzia),
J1745 (Infliximab/Remicade), J2182 (Mepolizumab/Nucala)

MEDICAL NECESSITY CRITERIA:
Prior authorization is REQUIRED for all biologic and biosimilar therapies.

STEP THERAPY REQUIREMENTS:
Patients must have documented trial and failure of conventional therapies before
biologic approval:
- Rheumatoid Arthritis: Failed 2+ conventional DMARDs (methotrexate required as first-line)
- Crohn's Disease: Failed conventional therapy (5-ASA, corticosteroids, immunomodulators)
- Psoriatic Arthritis: Failed 1+ conventional DMARD and 1+ NSAID
- Ankylosing Spondylitis: Failed 2+ NSAIDs

REQUIRED DOCUMENTATION:
1. Confirmed diagnosis with supporting laboratory and/or imaging evidence
2. Documentation of conventional therapy trials with dates, doses, and outcomes
3. Current disease activity score (DAS28, CDAI, BASDAI, or equivalent)
4. Tuberculosis screening (PPD or QuantiFERON) within 12 months
5. Hepatitis B and C screening results
6. Current vaccination status
7. Prescribing specialist credentials

REAUTHORIZATION:
- Required every 12 months
- Must document continued clinical response
- Disease activity score comparison from baseline

TYPICAL TURNAROUND: 5-10 business days
APPEAL WINDOW: 180 days
        """,
    },
    {
        "id": "AETNA-KNEE-001",
        "payer": "Aetna",
        "payer_id": "aetna",
        "category": "knee_replacement",
        "title": "Aetna Clinical Policy Bulletin: Knee Arthroplasty",
        "content": """
AETNA CLINICAL POLICY BULLETIN
Number: 0650
Subject: Total and Partial Knee Arthroplasty (CPT 27447, 27446)

POLICY:
Aetna considers total knee arthroplasty medically necessary when ALL of the following
criteria are met:

1. RADIOGRAPHIC EVIDENCE:
   - Weight-bearing anteroposterior and lateral radiographs obtained within 6 months
   - Kellgren-Lawrence Grade III or IV changes
   - Significant joint space narrowing, osteophytes, or bone-on-bone contact

2. BODY MASS INDEX:
   - BMI < 40 preferred
   - BMI 40-45: requires documentation of supervised weight management program
   - BMI > 45: generally not approved without bariatric surgery consultation

3. CONSERVATIVE TREATMENT:
   - Physical therapy completion (minimum 6 weeks, documented)
   - Failed pharmacological management (NSAIDs, analgesics)
   - At least one intra-articular injection (corticosteroid or hyaluronic acid)
   - Total conservative treatment period: minimum 3 months

4. SURGICAL EVALUATION:
   - Operative plan from board-certified orthopedic surgeon
   - Documentation of functional limitations
   - Patient has been informed of risks, benefits, and alternatives

AUTO-APPROVAL: Grade IV OA with failed 6+ months conservative treatment
TURNAROUND: 5 business days
APPEAL: 365 days
        """,
    },
    {
        "id": "AETNA-MRI-001",
        "payer": "Aetna",
        "payer_id": "aetna",
        "category": "MRI",
        "title": "Aetna Clinical Policy Bulletin: Advanced Imaging — MRI",
        "content": """
AETNA CLINICAL POLICY BULLETIN
Subject: Magnetic Resonance Imaging (MRI) Prior Authorization

POLICY:
Prior authorization is required for outpatient MRI studies.

APPROVAL CRITERIA:
1. Clinical indication supported by ICD-10 diagnosis code
2. Conservative treatment attempted for minimum 4 weeks (musculoskeletal indications)
3. Physical examination findings documented
4. Prior imaging (X-ray or CT) performed and results available

EXPEDITED APPROVAL (no wait):
- Emergency or trauma
- Cancer staging per NCCN guidelines
- Pre-surgical planning for previously approved procedure
- Acute neurological symptoms

SPECIFIC GUIDELINES:
Lumbar/Cervical Spine MRI:
- Minimum 4 weeks of symptoms
- Failed conservative treatment (medication + PT or home exercise)
- Neurological signs on examination preferred but not required
- Red flag symptoms bypass waiting period

Brain MRI:
- New neurological symptoms
- Change in headache pattern with red flag features
- Follow-up of known intracranial pathology
- Seizure workup

TURNAROUND: 2 business days
APPEAL: 365 days from denial
        """,
    },
    {
        "id": "BCBS-KNEE-001",
        "payer": "Blue Cross Blue Shield",
        "payer_id": "blue_cross_blue_shield",
        "category": "knee_replacement",
        "title": "BCBS Medical Policy: Total Knee Replacement Surgery",
        "content": """
BLUE CROSS BLUE SHIELD MEDICAL POLICY
Policy Number: SUR-2024-0234
Subject: Total Knee Arthroplasty

COVERAGE DETERMINATION:
Total knee arthroplasty is covered when medically necessary.

MEDICAL NECESSITY REQUIREMENTS:
1. Radiographic evidence of severe arthritis (Kellgren-Lawrence III-IV)
   documented on weight-bearing films within 6 months
2. Documented failure of non-surgical management for minimum 3 months including:
   - Structured physical therapy program
   - Pharmacological therapy (NSAIDs, analgesics)
   - At least one injection therapy (corticosteroid or viscosupplementation)
3. Functional limitation documentation using validated instrument
4. Medical necessity letter from board-certified orthopedic surgeon
5. Pre-operative medical clearance from primary care physician

SPECIAL CONSIDERATIONS:
- Revision arthroplasty: covered for mechanical failure or infection
- Bilateral simultaneous: requires additional justification and medical clearance
- Robotic-assisted: covered at same rate as conventional

AUTO-APPROVAL:
- Revision of previously approved arthroplasty
- Fracture requiring arthroplasty (emergent)

TURNAROUND: 3-5 business days
APPEAL: 180 days
        """,
    },
    {
        "id": "BCBS-MRI-001",
        "payer": "Blue Cross Blue Shield",
        "payer_id": "blue_cross_blue_shield",
        "category": "MRI",
        "title": "BCBS Medical Policy: Advanced Diagnostic Imaging — MRI",
        "content": """
BLUE CROSS BLUE SHIELD MEDICAL POLICY
Policy Number: RAD-2024-0089
Subject: Magnetic Resonance Imaging Prior Authorization

PRIOR AUTHORIZATION REQUIRED for all outpatient MRI studies.

APPROVAL CRITERIA:
1. Order from treating physician with documented clinical rationale
2. Duration and nature of symptoms described
3. Conservative treatment history (minimum 4-6 weeks for non-urgent)
4. Relevant physical examination findings documented
5. Prior imaging results if applicable

RED FLAG EXEMPTIONS (immediate approval):
- Progressive neurological deficit
- Suspected cauda equina syndrome
- New onset seizure
- Suspected malignancy with clinical urgency
- Post-traumatic with neurological findings

CANCER SURVEILLANCE:
- Approved per NCCN guidelines without additional review
- Frequency per guideline protocol

POST-OPERATIVE:
- Approved within 6 months of surgery without additional review

TURNAROUND: 2-3 business days
APPEAL: 180 days
        """,
    },
]


def _tokenize(text: str) -> list[str]:
    """Simple tokenizer: lowercase, split on non-alphanumeric, remove stopwords."""
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "shall",
        "should", "may", "might", "must", "can", "could", "of", "in", "to",
        "for", "with", "on", "at", "from", "by", "about", "as", "into",
        "through", "during", "before", "after", "above", "below", "between",
        "and", "but", "or", "nor", "not", "so", "yet", "both", "either",
        "neither", "each", "every", "all", "any", "few", "more", "most",
        "other", "some", "such", "no", "only", "own", "same", "than",
        "too", "very", "just", "because", "if", "when", "while", "this",
        "that", "these", "those", "it", "its", "i", "me", "my", "we", "our",
        "you", "your", "he", "him", "his", "she", "her", "they", "them", "their",
    }
    tokens = re.findall(r'[a-z0-9]+', text.lower())
    return [t for t in tokens if t not in stopwords and len(t) > 1]


class RAGEngine:
    """
    TF-IDF based vector search engine for policy document retrieval.
    Demonstrates the RAG (Retrieval-Augmented Generation) pattern.
    """

    def __init__(self):
        self.documents = POLICY_DOCUMENTS
        self.vocab: dict[str, int] = {}
        self.idf: dict[str, float] = {}
        self.doc_vectors: list[np.ndarray] = []
        self._initialized = False

    def initialize(self):
        """Build TF-IDF index over all policy documents."""
        if self._initialized:
            return

        print("RAG Engine: Building TF-IDF vector index over policy documents...")

        # Tokenize all documents
        doc_tokens = [_tokenize(doc["content"]) for doc in self.documents]

        # Build vocabulary
        all_tokens = set()
        for tokens in doc_tokens:
            all_tokens.update(tokens)
        self.vocab = {token: i for i, token in enumerate(sorted(all_tokens))}

        # Compute IDF
        n_docs = len(doc_tokens)
        doc_freq = Counter()
        for tokens in doc_tokens:
            doc_freq.update(set(tokens))
        self.idf = {
            token: math.log((n_docs + 1) / (df + 1)) + 1
            for token, df in doc_freq.items()
        }

        # Compute TF-IDF vectors for each document
        self.doc_vectors = []
        for tokens in doc_tokens:
            vec = np.zeros(len(self.vocab))
            tf = Counter(tokens)
            for token, count in tf.items():
                if token in self.vocab:
                    vec[self.vocab[token]] = (1 + math.log(count)) * self.idf.get(token, 1)
            # L2 normalize
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec /= norm
            self.doc_vectors.append(vec)

        self._initialized = True
        print(f"RAG Engine: Indexed {len(self.documents)} documents, {len(self.vocab)} terms.")

    def search(self, query: str, top_k: int = 3, payer_filter: str = None) -> list[dict]:
        """
        Semantic search over policy documents using TF-IDF cosine similarity.

        Args:
            query: Natural language search query
            top_k: Number of results to return
            payer_filter: Optional payer ID to filter results

        Returns:
            List of matching documents with similarity scores
        """
        if not self._initialized:
            self.initialize()

        # Vectorize the query
        tokens = _tokenize(query)
        query_vec = np.zeros(len(self.vocab))
        tf = Counter(tokens)
        for token, count in tf.items():
            if token in self.vocab:
                query_vec[self.vocab[token]] = (1 + math.log(count)) * self.idf.get(token, 1)
        norm = np.linalg.norm(query_vec)
        if norm > 0:
            query_vec /= norm

        # Compute cosine similarity against all documents
        results = []
        for i, doc in enumerate(self.documents):
            if payer_filter and doc["payer_id"] != payer_filter:
                continue

            similarity = float(np.dot(query_vec, self.doc_vectors[i]))
            results.append({
                "document_id": doc["id"],
                "payer": doc["payer"],
                "category": doc["category"],
                "title": doc["title"],
                "content": doc["content"].strip(),
                "similarity_score": round(similarity, 4),
            })

        # Sort by similarity and return top_k
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_k]


# Singleton instance
rag_engine = RAGEngine()
