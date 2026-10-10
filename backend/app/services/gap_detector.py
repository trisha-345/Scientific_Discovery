"""
Gap detector — delegates to semantic version when embeddings available,
falls back to legacy keyword rules otherwise.
"""
from typing import List, Dict
from sqlalchemy.orm import Session
from app import models
from app.services.semantic_gaps import detect_semantic_gaps


def detect_gaps(db: Session, project_id: int) -> List[Dict]:
    """Detect research gaps. Prefers semantic method; falls back to legacy."""
    try:
        gaps = detect_semantic_gaps(db, project_id)
        if gaps:
            return gaps
    except Exception as e:
        print(f"[gap_detector] semantic detection failed, falling back: {e}")

    return _legacy_detect_gaps(db, project_id)


# ---------- legacy fallback ----------
def _legacy_detect_gaps(db: Session, project_id: int) -> List[Dict]:
    from collections import Counter

    papers = db.query(models.Paper).filter_by(project_id=project_id).all()
    if not papers:
        return []

    gaps = []

    lims = [(p.id, c.text) for p in papers for c in p.claims if c.claim_type == "limitation"]
    if lims:
        gaps.append({
            "gap_type": "methodological",
            "title": f"{len(lims)} limitations cited across {len(papers)} papers",
            "description": "Recurring limitations suggest under-explored methodological directions.",
            "evidence": [{"paper_id": pid, "claim": t} for pid, t in lims[:15]],
            "opportunity_score": min(100.0, 40 + len(lims) * 5),
        })

    short = sum(1 for p in papers if "short-term" in (p.full_text or "").lower())
    long_ = sum(1 for p in papers if "long-term" in (p.full_text or "").lower()
                or "longitudinal" in (p.full_text or "").lower())
    if short > long_:
        gaps.append({
            "gap_type": "temporal",
            "title": "Long-term effects under-studied",
            "description": f"{short} short-term vs {long_} long-term studies.",
            "evidence": [{"paper_id": p.id} for p in papers],
            "opportunity_score": 75.0,
        })

    pos = [p.id for p in papers if "significantly improved" in (p.full_text or "").lower()]
    neg = [p.id for p in papers if "no significant improvement" in (p.full_text or "").lower()]
    if pos and neg:
        gaps.append({
            "gap_type": "contradiction",
            "title": "Contradictory findings detected",
            "description": "Some papers report improvement; others report no effect.",
            "evidence": [{"paper_id": i, "stance": "positive"} for i in pos]
                      + [{"paper_id": i, "stance": "negative"} for i in neg],
            "opportunity_score": 85.0,
        })

    geo = Counter()
    for p in papers:
        low = (p.full_text or "").lower()
        for r in ["usa", "europe", "china", "india", "africa", "uk"]:
            if r in low:
                geo[r] += 1
    if geo and (geo.get("india", 0) < 2):
        gaps.append({
            "gap_type": "geographic",
            "title": "Limited geographic diversity",
            "description": f"Regions detected: {dict(geo)}",
            "evidence": [{"region": r, "count": c} for r, c in geo.items()],
            "opportunity_score": 65.0,
        })

    return gaps