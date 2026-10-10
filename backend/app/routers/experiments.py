from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.services.experiment_planner import generate_experiment_plan, plan_to_markdown

router = APIRouter(prefix="/api/hypotheses", tags=["experiments"])


@router.post("/{hypothesis_id}/plan")
def create_experiment_plan(hypothesis_id: int, db: Session = Depends(get_db)):
    """Generate an experiment plan for a hypothesis using Groq."""
    h = db.get(models.Hypothesis, hypothesis_id)
    if not h:
        raise HTTPException(404, "Hypothesis not found")

    # Reuse existing plan if one exists
    existing = (
        db.query(models.ExperimentPlan)
        .filter_by(hypothesis_id=hypothesis_id)
        .order_by(models.ExperimentPlan.created_at.desc())
        .first()
    )
    if existing:
        return {
            "plan_id": existing.id,
            "hypothesis_id": hypothesis_id,
            "plan": existing.plan,
            "markdown": existing.markdown,
            "cached": True,
        }

    # Generate fresh
    hyp_dict = {
        "text": h.text,
        "null_hypothesis": h.null_hypothesis,
        "independent_var": h.independent_var,
        "dependent_var": h.dependent_var,
        "control_vars": h.control_vars,
        "overall_score": h.overall_score,
    }

    try:
        plan = generate_experiment_plan(hyp_dict)
        markdown = plan_to_markdown(plan, h.text)
    except Exception as e:
        raise HTTPException(500, f"Experiment planner failed: {e}")

    row = models.ExperimentPlan(
        project_id=h.project_id,
        hypothesis_id=h.id,
        plan=plan,
        markdown=markdown,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return {
        "plan_id": row.id,
        "hypothesis_id": hypothesis_id,
        "plan": plan,
        "markdown": markdown,
        "cached": False,
    }


@router.get("/{hypothesis_id}/plan")
def get_experiment_plan(hypothesis_id: int, db: Session = Depends(get_db)):
    """Fetch the most recent experiment plan for a hypothesis."""
    row = (
        db.query(models.ExperimentPlan)
        .filter_by(hypothesis_id=hypothesis_id)
        .order_by(models.ExperimentPlan.created_at.desc())
        .first()
    )
    if not row:
        raise HTTPException(404, "No experiment plan yet")

    return {
        "plan_id": row.id,
        "hypothesis_id": hypothesis_id,
        "plan": row.plan,
        "markdown": row.markdown,
        "cached": True,
    }


@router.delete("/{hypothesis_id}/plan")
def delete_experiment_plan(hypothesis_id: int, db: Session = Depends(get_db)):
    """Regenerate a plan on next request by deleting existing ones."""
    db.query(models.ExperimentPlan).filter_by(hypothesis_id=hypothesis_id).delete()
    db.commit()
    return {"deleted": True}