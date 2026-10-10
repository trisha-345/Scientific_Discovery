from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas
from app.services.gap_detector import detect_gaps
from app.services.hypothesis_generator import generate_hypotheses

router = APIRouter(prefix="/api/analyze", tags=["analysis"])


@router.post("/{project_id}")
def analyze(project_id: int, db: Session = Depends(get_db)):
    if not db.get(models.Project, project_id):
        raise HTTPException(404, "Project not found")

    gaps_raw = detect_gaps(db, project_id)

    db.query(models.ResearchGap).filter_by(project_id=project_id).delete()
    db.query(models.Hypothesis).filter_by(project_id=project_id).delete()
    db.commit()

    saved = []
    for g in gaps_raw:
        row = models.ResearchGap(
            project_id=project_id,
            gap_type=g["gap_type"],
            title=g["title"],
            description=g["description"],
            evidence=g.get("evidence"),
            opportunity_score=g.get("opportunity_score", 0.0),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        saved.append({"row": row, "raw": g})

    hyps = generate_hypotheses([s["raw"] for s in saved])

    for item, sg in zip(hyps, saved):
        h = item["hypothesis"]
        s = item["scores"]
        db.add(models.Hypothesis(
            project_id=project_id,
            gap_id=sg["row"].id,
            text=h["text"],
            null_hypothesis=h["null"],
            independent_var=h["iv"],
            dependent_var=h["dv"],
            control_vars=h["controls"],
            novelty_score=s["novelty"],
            evidence_score=s["evidence"],
            testability_score=s["testability"],
            feasibility_score=s["feasibility"],
            overall_score=s["overall"],
            evidence_chain=item["evidence_chain"],
        ))
    db.commit()

    return {
        "gaps_found": len(saved),
        "hypotheses_generated": len(hyps),
        "gap_types": [g["gap_type"] for g in gaps_raw],
    }


@router.get("/{project_id}/gaps", response_model=List[schemas.GapOut])
def list_gaps(project_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.ResearchGap)
        .filter_by(project_id=project_id)
        .order_by(models.ResearchGap.opportunity_score.desc())
        .all()
    )


@router.get("/{project_id}/hypotheses", response_model=List[schemas.HypothesisOut])
def list_hypotheses(project_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Hypothesis)
        .filter_by(project_id=project_id)
        .order_by(models.Hypothesis.overall_score.desc())
        .all()
    )


@router.get("/{project_id}/graph")
def get_graph(project_id: int, db: Session = Depends(get_db)):
    """
    Return a knowledge graph for a project:
      - Project (root)
      - Papers (children of project)
      - Claims (children of papers)
      - Gaps (children of project)
      - Hypotheses (children of gaps)
    """
    project = db.get(models.Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    papers = db.query(models.Paper).filter_by(project_id=project_id).all()
    gaps = db.query(models.ResearchGap).filter_by(project_id=project_id).all()
    hypotheses = db.query(models.Hypothesis).filter_by(project_id=project_id).all()

    nodes = []
    edges = []

    # ---- Project node (root) ----
    nodes.append({
        "id": f"project-{project.id}",
        "type": "input",
        "data": {
            "label": project.name,
            "kind": "project",
            "detail": project.topic,
        },
        "position": {"x": 0, "y": 0},
    })

    # ---- Paper nodes + their Claims ----
    for i, p in enumerate(papers):
        pid = f"paper-{p.id}"
        nodes.append({
            "id": pid,
            "data": {
                "label": (p.title or "Untitled")[:40],
                "kind": "paper",
                "detail": p.abstract or "",
                "paper_id": p.id,
            },
            "position": {"x": -400, "y": i * 200},
        })
        edges.append({
            "id": f"e-proj-{pid}",
            "source": f"project-{project.id}",
            "target": pid,
            "type": "smoothstep",
            "style": {"stroke": "#22c55e", "strokeWidth": 2},
        })

        claims = db.query(models.Claim).filter_by(paper_id=p.id).all()
        for j, c in enumerate(claims[:8]):
            cid = f"claim-{c.id}"
            nodes.append({
                "id": cid,
                "data": {
                    "label": (c.text[:50] + "…") if len(c.text) > 50 else c.text,
                    "kind": "claim",
                    "detail": c.text,
                    "claim_type": c.claim_type,
                    "claim_id": c.id,
                    "paper_id": p.id,
                },
                "position": {"x": -800, "y": i * 200 + (j - 3) * 55},
            })
            edges.append({
                "id": f"e-{pid}-{cid}",
                "source": pid,
                "target": cid,
                "type": "smoothstep",
                "style": {"stroke": "#94a3b8", "strokeWidth": 1},
            })

    # ---- Gap nodes ----
    for i, g in enumerate(gaps):
        gid = f"gap-{g.id}"
        nodes.append({
            "id": gid,
            "data": {
                "label": g.title[:45],
                "kind": "gap",
                "detail": g.description,
                "gap_type": g.gap_type,
                "score": g.opportunity_score,
                "gap_id": g.id,
            },
            "position": {"x": 400, "y": i * 180},
        })
        edges.append({
            "id": f"e-proj-{gid}",
            "source": f"project-{project.id}",
            "target": gid,
            "type": "smoothstep",
            "style": {"stroke": "#f59e0b", "strokeWidth": 2},
        })

    # ---- Hypothesis nodes ----
    for i, h in enumerate(hypotheses):
        hid = f"hyp-{h.id}"
        nodes.append({
            "id": hid,
            "data": {
                "label": (h.text[:45] + "…") if len(h.text) > 45 else h.text,
                "kind": "hypothesis",
                "detail": h.text,
                "score": h.overall_score,
                "hyp_id": h.id,
                "gap_id": h.gap_id,
            },
            "position": {"x": 850, "y": i * 180},
        })
        if h.gap_id:
            edges.append({
                "id": f"e-gap-{h.gap_id}-hyp-{h.id}",
                "source": f"gap-{h.gap_id}",
                "target": hid,
                "type": "smoothstep",
                "animated": True,
                "style": {"stroke": "#8b5cf6", "strokeWidth": 2},
            })
        else:
            edges.append({
                "id": f"e-proj-{hid}",
                "source": f"project-{project.id}",
                "target": hid,
                "type": "smoothstep",
                "style": {"stroke": "#8b5cf6", "strokeWidth": 2},
            })

    return {"nodes": nodes, "edges": edges}