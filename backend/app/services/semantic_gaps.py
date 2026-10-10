"""
Semantic gap detection using embeddings + claim structure.

Replaces the crude keyword rules with:
- Clustering of claims by embedding similarity
- Contradiction detection via polarity mismatch
- Under-studied combos (subject × method × population)
"""
import re
from collections import defaultdict, Counter
from typing import List, Dict
import numpy as np
from sqlalchemy.orm import Session
from app import models
from app.services.embeddings import get_model


# ---------- polarity lexicon (small, extend as needed) ----------
POSITIVE_WORDS = {
    "improve", "improved", "improves", "increase", "increased", "increases",
    "better", "enhance", "enhanced", "higher", "gain", "gains", "boost", "boosts",
    "effective", "efficacious", "helpful", "superior", "outperforms", "outperformed",
    "significant", "significantly", "positive", "success", "succeeded",
}
NEGATIVE_WORDS = {
    "decrease", "decreased", "decreases", "reduce", "reduced", "reduces",
    "worse", "lower", "harm", "harmful", "harmful", "fail", "failed", "fails",
    "ineffective", "no effect", "no significant", "not significant", "not improve",
    "not improved", "no improvement", "unhelpful", "detrimental", "negative",
    "counterproductive",
}


def _polarity(text: str) -> float:
    """Return -1 (negative), 0 (neutral), +1 (positive) based on words present."""
    t = text.lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in t)
    neg = sum(1 for w in NEGATIVE_WORDS if w in t)
    if pos > neg:
        return 1.0
    if neg > pos:
        return -1.0
    return 0.0


# ---------- geography / time / method extraction ----------
COUNTRIES = [
    "usa", "united states", "uk", "united kingdom", "china", "india", "japan",
    "germany", "france", "italy", "spain", "canada", "australia", "brazil",
    "russia", "south korea", "singapore", "africa", "europe", "asia",
]

TIME_HORIZONS = {
    "short": ["short-term", "immediate", "one month", "1 month", "few weeks", "short run"],
    "long":  ["long-term", "longitudinal", "follow-up", "one year", "5-year", "years later"],
}


def _find_countries(text: str) -> List[str]:
    t = text.lower()
    return [c for c in COUNTRIES if c in t]


def _find_time_horizon(text: str) -> str:
    t = text.lower()
    long_hits = sum(1 for kw in TIME_HORIZONS["long"] if kw in t)
    short_hits = sum(1 for kw in TIME_HORIZONS["short"] if kw in t)
    if long_hits > short_hits:
        return "long"
    if short_hits > long_hits:
        return "short"
    return "unknown"


# ---------- main detector ----------
def detect_semantic_gaps(db: Session, project_id: int) -> List[Dict]:
    """Return list of gap dicts (same shape as legacy detect_gaps)."""
    papers = db.query(models.Paper).filter_by(project_id=project_id).all()
    if not papers:
        return []

    # Gather all claims with their embeddings (paper-level)
    claims: List[models.Claim] = []
    paper_by_id = {p.id: p for p in papers}
    for p in papers:
        claims.extend(p.claims)

    gaps: List[Dict] = []

    # ---- 1. CONTRADICTION GAP (semantic, uses embeddings) ----
    contradiction_gap = _contradiction_gap(claims, paper_by_id)
    if contradiction_gap:
        gaps.append(contradiction_gap)

    # ---- 2. POPULATION / SUBJECT GAP (under-studied subjects) ----
    population_gap = _subject_scarcity_gap(claims, paper_by_id)
    if population_gap:
        gaps.append(population_gap)

    # ---- 3. GEOGRAPHIC GAP ----
    geo_gap = _geographic_gap(papers)
    if geo_gap:
        gaps.append(geo_gap)

    # ---- 4. TEMPORAL GAP ----
    temporal_gap = _temporal_gap(papers)
    if temporal_gap:
        gaps.append(temporal_gap)

    # ---- 5. METHODOLOGICAL GAP ----
    method_gap = _method_gap(claims, paper_by_id)
    if method_gap:
        gaps.append(method_gap)

    # Assign an opportunity score to each
    for g in gaps:
        g["opportunity_score"] = _score_gap(g, papers)

    # Sort by score descending
    gaps.sort(key=lambda x: -x["opportunity_score"])

    return gaps


# ---------- individual detectors ----------

def _contradiction_gap(claims: List[models.Claim], paper_by_id: dict) -> Dict | None:
    """Find pairs of claims that talk about the same thing but disagree in polarity."""
    if len(claims) < 2:
        return None

    # Compute polarity for each claim
    polarities = [(_polarity(c.text), c) for c in claims]
    pos_claims = [c for pol, c in polarities if pol > 0]
    neg_claims = [c for pol, c in polarities if pol < 0]

    if not pos_claims or not neg_claims:
        return None

    # Use existing embeddings: find most similar opposite-polarity pair
    model = get_model()

    pos_texts = [c.text[:500] for c in pos_claims]
    neg_texts = [c.text[:500] for c in neg_claims]

    pos_vecs = model.encode(pos_texts, normalize_embeddings=True, show_progress_bar=False)
    neg_vecs = model.encode(neg_texts, normalize_embeddings=True, show_progress_bar=False)

    # Similarity matrix
    sims = pos_vecs @ neg_vecs.T  # shape (n_pos, n_neg)

    # Best contradictory pair
    best_i, best_j = np.unravel_index(np.argmax(sims), sims.shape)
    best_sim = float(sims[best_i, best_j])

    # Only report if they're actually talking about the same thing
    if best_sim < 0.45:
        return None

    c_pos = pos_claims[best_i]
    c_neg = neg_claims[best_j]

    evidence = [
        {"paper_id": c_pos.paper_id, "claim_id": c_pos.id, "stance": "positive", "text": c_pos.text[:300]},
        {"paper_id": c_neg.paper_id, "claim_id": c_neg.id, "stance": "negative", "text": c_neg.text[:300]},
    ]

    return {
        "gap_type": "contradiction",
        "title": f"Contradictory findings detected (semantic sim: {best_sim:.2f})",
        "description": (
            f"Two papers discuss the same topic but disagree in polarity. "
            f"Similarity: {best_sim:.2f}. Investigating moderators could resolve the disagreement."
        ),
        "evidence": evidence,
        "confidence": best_sim,
    }


def _subject_scarcity_gap(claims: List[models.Claim], paper_by_id: dict) -> Dict | None:
    """Find subjects that appear in very few papers (under-studied populations)."""
    if not claims:
        return None

    # Group claims by normalized subject
    subject_to_papers = defaultdict(set)
    subject_to_claims = defaultdict(list)

    for c in claims:
        if not c.subject:
            continue
        subj = c.subject.strip().lower()
        if len(subj) < 3:
            continue
        subject_to_papers[subj].add(c.paper_id)
        subject_to_claims[subj].append(c)

    total_papers = len(paper_by_id)
    if total_papers < 2:
        return None

    # Subjects that appear in exactly 1 paper but the paper mentions ≥3 claims about it
    scarce = []
    for subj, papers_set in subject_to_papers.items():
        if len(papers_set) == 1 and len(subject_to_claims[subj]) >= 2:
            scarce.append((subj, papers_set.pop(), subject_to_claims[subj]))

    if not scarce:
        return None

    # Pick the most "central" one (longest subject name = more informative)
    scarce.sort(key=lambda x: -len(x[0]))
    subj, paper_id, clms = scarce[0]

    return {
        "gap_type": "population",
        "title": f"Only one paper studies '{subj}'",
        "description": (
            f"'{subj}' appears in {len(clms)} claims but only from a single paper. "
            "Replication or extension to other contexts is warranted."
        ),
        "evidence": [
            {"paper_id": paper_id, "claim_id": c.id, "text": c.text[:200]}
            for c in clms[:5]
        ],
    }


def _geographic_gap(papers: List[models.Paper]) -> Dict | None:
    """Detect under-represented geographic regions."""
    region_counter = Counter()
    for p in papers:
        countries = _find_countries((p.full_text or "")[:20000])
        for c in set(countries):
            region_counter[c] += 1

    if not region_counter:
        return None

    total = sum(region_counter.values())
    # Find the dominant region
    dominant, dom_count = region_counter.most_common(1)[0]

    # Under-represented: any region mentioned < 30% of dominant
    underrepresented = [
        (r, c) for r, c in region_counter.items()
        if c < dom_count * 0.5 and r != dominant
    ]

    # Or the whole geo distribution is heavily skewed
    if not underrepresented and dom_count / total > 0.6 and total >= 3:
        underrepresented = [("non-" + dominant, 0)]

    if not underrepresented:
        return None

    return {
        "gap_type": "geographic",
        "title": f"Geographic over-representation of '{dominant}'",
        "description": (
            f"'{dominant}' appears in {dom_count}/{len(papers)} papers. "
            f"Other regions are under-represented. Consider replicating in "
            f"{', '.join(r for r, _ in underrepresented[:3])}."
        ),
        "evidence": [
            {"region": r, "paper_count": c} for r, c in region_counter.most_common()
        ],
    }


def _temporal_gap(papers: List[models.Paper]) -> Dict | None:
    """Detect over-focus on short-term vs long-term studies."""
    counter = Counter()
    for p in papers:
        horizon = _find_time_horizon((p.full_text or "")[:20000])
        if horizon != "unknown":
            counter[horizon] += 1

    if counter["short"] == 0 and counter["long"] == 0:
        return None
    if counter["short"] <= counter["long"]:
        return None

    return {
        "gap_type": "temporal",
        "title": f"Over-focus on short-term outcomes ({counter['short']} vs {counter['long']})",
        "description": (
            f"{counter['short']} papers study short-term effects, only "
            f"{counter['long']} study long-term. Long-term generalization is unclear."
        ),
        "evidence": [
            {"paper_id": p.id, "title": p.title}
            for p in papers
            if _find_time_horizon((p.full_text or "")[:20000]) == "short"
        ][:8],
    }


def _method_gap(claims: List[models.Claim], paper_by_id: dict) -> Dict | None:
    """Find methods that appear rarely."""
    methods = [c for c in claims if c.claim_type == "method"]
    if not methods:
        # fallback to limitations count
        limitations = [c for c in claims if c.claim_type == "limitation"]
        if len(limitations) >= 2:
            return {
                "gap_type": "methodological",
                "title": f"{len(limitations)} limitations noted across {len(paper_by_id)} papers",
                "description": "Recurring limitations suggest under-explored methodological directions.",
                "evidence": [
                    {"paper_id": c.paper_id, "claim_id": c.id, "text": c.text[:200]}
                    for c in limitations[:10]
                ],
            }
        return None

    # Group by method property
    method_counter = Counter()
    method_papers = defaultdict(set)
    for m in methods:
        key = (m.claim_property or m.claim_value or "unknown").strip().lower()
        if len(key) < 3:
            continue
        method_counter[key] += 1
        method_papers[key].add(m.paper_id)

    if not method_counter:
        return None

    # Rare methods used in only 1 paper
    rare = [(k, v) for k, v in method_counter.items() if len(method_papers[k]) == 1]
    if not rare:
        return None

    rare.sort(key=lambda x: -x[1])
    method, count = rare[0]

    return {
        "gap_type": "methodological",
        "title": f"Method '{method}' used in only one paper",
        "description": (
            f"'{method}' appears {count} times but only from one study. "
            "Replication with this method is warranted."
        ),
        "evidence": [
            {"paper_id": m.paper_id, "claim_id": m.id, "text": m.text[:200]}
            for m in methods
            if (m.claim_property or m.claim_value or "").strip().lower() == method
        ][:5],
    }


# ---------- scoring ----------

def _score_gap(gap: Dict, papers: List[models.Paper]) -> float:
    """Compute opportunity score 0-100 based on gap properties."""
    base = 40.0

    gap_type = gap.get("gap_type")
    type_bonus = {
        "contradiction": 30,
        "population": 20,
        "geographic": 15,
        "temporal": 20,
        "methodological": 15,
    }.get(gap_type, 0)
    base += type_bonus

    # Evidence count bonus
    evidence = gap.get("evidence") or []
    base += min(20.0, len(evidence) * 3)

    # Contradiction confidence bonus
    if "confidence" in gap:
        base += gap["confidence"] * 10

    return min(100.0, round(base, 1))