"""
Semantic gap detection using keyword + claim structure.

NOTE: This version does NOT use embeddings (sentence-transformers).
It's designed for memory-constrained deployments (Render free tier, 512 MB).
Gap detection is keyword- and structure-based.
"""
from collections import defaultdict, Counter
from typing import List, Dict
from sqlalchemy.orm import Session
from app import models


# ---------- polarity lexicon ----------
POSITIVE_WORDS = {
    "improve", "improved", "improves", "increase", "increased", "increases",
    "better", "enhance", "enhanced", "higher", "gain", "gains", "boost", "boosts",
    "effective", "efficacious", "helpful", "superior", "outperforms", "outperformed",
    "significant", "significantly", "positive", "success", "succeeded",
}
NEGATIVE_WORDS = {
    "decrease", "decreased", "decreases", "reduce", "reduced", "reduces",
    "worse", "lower", "harm", "harmful", "fail", "failed", "fails",
    "ineffective", "no effect", "no significant", "not significant", "not improve",
    "not improved", "no improvement", "unhelpful", "detrimental", "negative",
    "counterproductive",
}

COUNTRIES = [
    "usa", "united states", "uk", "united kingdom", "china", "india", "japan",
    "germany", "france", "italy", "spain", "canada", "australia", "brazil",
    "russia", "south korea", "singapore", "africa", "europe", "asia",
]

TIME_HORIZONS = {
    "short": ["short-term", "immediate", "one month", "1 month", "few weeks", "short run"],
    "long":  ["long-term", "longitudinal", "follow-up", "one year", "5-year", "years later"],
}


def _polarity(text: str) -> float:
    t = text.lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in t)
    neg = sum(1 for w in NEGATIVE_WORDS if w in t)
    if pos > neg:
        return 1.0
    if neg > pos:
        return -1.0
    return 0.0


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


def detect_semantic_gaps(db: Session, project_id: int) -> List[Dict]:
    """Return list of gap dicts."""
    papers = db.query(models.Paper).filter_by(project_id=project_id).all()
    if not papers:
        return []

    claims: List[models.Claim] = []
    paper_by_id = {p.id: p for p in papers}
    for p in papers:
        claims.extend(p.claims)

    gaps: List[Dict] = []

    c = _contradiction_gap(claims)
    if c:
        gaps.append(c)

    p = _subject_scarcity_gap(claims, paper_by_id)
    if p:
        gaps.append(p)

    g = _geographic_gap(papers)
    if g:
        gaps.append(g)

    t = _temporal_gap(papers)
    if t:
        gaps.append(t)

    m = _method_gap(claims, paper_by_id)
    if m:
        gaps.append(m)

    for gap in gaps:
        gap["opportunity_score"] = _score_gap(gap, papers)

    gaps.sort(key=lambda x: -x["opportunity_score"])
    return gaps


# ---------- individual detectors ----------

def _contradiction_gap(claims: List[models.Claim]) -> Dict | None:
    if len(claims) < 2:
        return None

    pos_claims = [c for c in claims if _polarity(c.text) > 0]
    neg_claims = [c for c in claims if _polarity(c.text) < 0]

    if not pos_claims or not neg_claims:
        return None

    return {
        "gap_type": "contradiction",
        "title": f"Contradictory findings detected ({len(pos_claims)} positive vs {len(neg_claims)} negative)",
        "description": (
            "Both positive and negative claims about the same topic exist in the literature. "
            "Investigating moderators (population, method, context) could resolve the disagreement."
        ),
        "evidence": [
            {"paper_id": c.paper_id, "claim_id": c.id, "stance": "positive", "text": c.text[:200]}
            for c in pos_claims[:3]
        ] + [
            {"paper_id": c.paper_id, "claim_id": c.id, "stance": "negative", "text": c.text[:200]}
            for c in neg_claims[:3]
        ],
    }


def _subject_scarcity_gap(claims: List[models.Claim], paper_by_id: dict) -> Dict | None:
    if not claims:
        return None

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

    scarce = []
    for subj, papers_set in subject_to_papers.items():
        if len(papers_set) == 1 and len(subject_to_claims[subj]) >= 2:
            scarce.append((subj, list(papers_set)[0], subject_to_claims[subj]))

    if not scarce:
        return None

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
    region_counter = Counter()
    for p in papers:
        countries = _find_countries((p.full_text or "")[:20000])
        for c in set(countries):
            region_counter[c] += 1

    if not region_counter:
        return None

    total = sum(region_counter.values())
    dominant, dom_count = region_counter.most_common(1)[0]

    underrepresented = [
        (r, c) for r, c in region_counter.items()
        if c < dom_count * 0.5 and r != dominant
    ]

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
    methods = [c for c in claims if c.claim_type == "method"]
    if not methods:
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


def _score_gap(gap: Dict, papers: List[models.Paper]) -> float:
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

    evidence = gap.get("evidence") or []
    base += min(20.0, len(evidence) * 3)

    return min(100.0, round(base, 1))