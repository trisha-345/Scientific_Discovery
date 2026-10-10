from typing import Dict, List
from app.services.llm_client import call_llm_json


SYSTEM_PROMPT = """You are a scientific hypothesis generation engine.
Given a detected research gap, generate a testable research hypothesis.
Return ONLY a JSON object with this exact shape:

{
  "text": "H1 — the main hypothesis statement, one to two sentences",
  "null": "H0 — the null hypothesis",
  "iv": "independent variable (be specific)",
  "dv": "dependent variable (be specific)",
  "controls": ["control var 1", "control var 2"],
  "novelty": 0-100,
  "evidence": 0-100,
  "testability": 0-100,
  "feasibility": 0-100,
  "reasoning": "one sentence explaining why this hypothesis matters"
}

Be specific to the gap. Mention concrete concepts, populations, or methods from the gap description.
Do not use generic phrases like "unmeasured contextual variable" or "methodological variation".
"""


def generate_hypotheses(gaps: List[Dict]) -> List[Dict]:
    """Generate a hypothesis for each detected gap using Groq."""
    results = []

    for gap in gaps:
        user_prompt = f"""Research gap detected:

Type: {gap.get('gap_type')}
Title: {gap.get('title')}
Description: {gap.get('description')}
Evidence items: {len(gap.get('evidence') or [])}
Opportunity score: {gap.get('opportunity_score', 0)}

Generate a specific, testable hypothesis that directly addresses this gap.
Reference the actual concepts in the description — do not use generic placeholders."""

        try:
            h = call_llm_json(SYSTEM_PROMPT, user_prompt)
            preview = (h.get("text") or "")[:80]
            print(f"[hypothesis_generator] Groq OK [{gap.get('gap_type')}]: {preview}...")
        except Exception as e:
            print(f"[hypothesis_generator] Groq error: {e}")
            h = {
                "text": f"Addressing the {gap.get('gap_type')} gap changes outcomes.",
                "null": "No significant effect.",
                "iv": "IV",
                "dv": "DV",
                "controls": [],
                "novelty": 60,
                "evidence": 60,
                "testability": 80,
                "feasibility": 75,
                "reasoning": "Fallback due to LLM error.",
            }

        overall = (
            0.30 * h.get("novelty", 50)
            + 0.25 * h.get("evidence", 50)
            + 0.25 * h.get("testability", 50)
            + 0.20 * h.get("feasibility", 50)
        )

        results.append({
            "gap": gap,
            "hypothesis": h,
            "scores": {
                "novelty": h.get("novelty", 50),
                "evidence": h.get("evidence", 50),
                "testability": h.get("testability", 50),
                "feasibility": h.get("feasibility", 50),
                "overall": round(overall, 2),
            },
            "evidence_chain": [
                {"role": "supports" if i % 2 == 0 else "context", "evidence": ev}
                for i, ev in enumerate((gap.get("evidence") or [])[:6])
            ],
        })

    return results