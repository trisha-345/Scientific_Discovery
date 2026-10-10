from typing import List, Dict
from app.services.llm_client import call_llm_json


SYSTEM_PROMPT = """You are a scientific claim extraction engine.
Extract every research claim, finding, and limitation from the given paper text.
Return ONLY a JSON object with this exact shape:

{
  "claims": [
    {
      "text": "the claim exactly as stated",
      "subject": "main subject (e.g. 'proposed model', 'AI tutoring')",
      "relationship": "verb relation (e.g. 'increased', 'reduced', 'causes')",
      "property": "measured property (e.g. 'accuracy', 'retention')",
      "value": "numeric or qualitative value (e.g. '12%', 'significantly')",
      "comparison": "baseline or comparison group (e.g. 'baseline model')",
      "claim_type": "finding | limitation | method | hypothesis | conclusion",
      "confidence": 0.0 to 1.0
    }
  ]
}

Guidelines:
- Extract findings: what the study discovered (performance, outcomes, effects)
- Extract limitations: what the authors say is missing or weak
- Extract methods only if they're central to the paper's contribution
- Skip generic background statements
- Aim for 5-15 claims per paper
"""


def extract_claims_from_paper(parsed: dict) -> List[Dict]:
    """Send paper text to Groq for structured claim extraction."""
    text = parsed.get("full_text") or ""
    if len(text) < 200:
        return []

    # Truncate to stay under token limits (roughly 12k chars ≈ 3k tokens)
    snippet = text[:15000]

    user_prompt = f"""Paper title: {parsed.get('title', 'Unknown')}

Abstract: {parsed.get('abstract', '')[:1000]}

Full text (truncated):
{snippet}

Extract all claims from this paper following the system instructions."""

    try:
        result = call_llm_json(SYSTEM_PROMPT, user_prompt)
    except Exception as e:
        print(f"[claim_extractor] Groq error: {e}")
        return []

    claims = result.get("claims", []) if isinstance(result, dict) else []
    # Normalize: ensure required keys
    normalized = []
    for c in claims:
        if not c.get("text"):
            continue
        normalized.append({
            "text": c.get("text", ""),
            "subject": c.get("subject"),
            "relationship_type": c.get("relationship"),
            "claim_property": c.get("property"),
            "claim_value": c.get("value"),
            "comparison": c.get("comparison"),
            "claim_type": c.get("claim_type", "finding"),
            "confidence": float(c.get("confidence", 0.6)),
        })
    return normalized