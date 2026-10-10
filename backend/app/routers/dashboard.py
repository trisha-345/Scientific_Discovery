from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=schemas.DashboardStats)
def stats(db: Session = Depends(get_db)):
    return schemas.DashboardStats(
        projects=db.query(models.Project).count(),
        papers=db.query(models.Paper).count(),
        gaps=db.query(models.ResearchGap).count(),
        hypotheses=db.query(models.Hypothesis).count(),
    )
