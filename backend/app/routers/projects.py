from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=schemas.ProjectOut)
def create_project(payload: schemas.ProjectCreate, db: Session = Depends(get_db)):
    p = models.Project(**payload.model_dump())
    db.add(p); db.commit(); db.refresh(p)
    return p


@router.get("", response_model=List[schemas.ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).order_by(models.Project.id.desc()).all()


@router.get("/{project_id}", response_model=schemas.ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    p = db.get(models.Project, project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    return p
