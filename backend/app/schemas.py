from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class ProjectCreate(BaseModel):
    name: str
    topic: str
    research_area: Optional[str] = "General"


class ProjectOut(BaseModel):
    id: int
    name: str
    topic: str
    research_area: str
    created_at: datetime
    class Config:
        from_attributes = True


class PaperOut(BaseModel):
    id: int
    title: Optional[str]
    abstract: Optional[str]
    class Config:
        from_attributes = True


class GapOut(BaseModel):
    id: int
    gap_type: str
    title: str
    description: str
    evidence: Optional[List[Any]]
    opportunity_score: float
    class Config:
        from_attributes = True


class HypothesisOut(BaseModel):
    id: int
    text: str
    null_hypothesis: Optional[str]
    independent_var: Optional[str]
    dependent_var: Optional[str]
    control_vars: Optional[List[str]]
    novelty_score: float
    evidence_score: float
    testability_score: float
    feasibility_score: float
    overall_score: float
    evidence_chain: Optional[List[Dict[str, Any]]]
    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    projects: int
    papers: int
    gaps: int
    hypotheses: int
