from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    topic = Column(Text, nullable=False)
    research_area = Column(String(128), default="General")
    created_at = Column(DateTime, default=datetime.utcnow)

    papers = relationship("Paper", back_populates="project", cascade="all, delete")
    gaps = relationship("ResearchGap", back_populates="project", cascade="all, delete")
    hypotheses = relationship("Hypothesis", back_populates="project", cascade="all, delete")


class Paper(Base):
    __tablename__ = "papers"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(512))
    abstract = Column(Text)
    full_text = Column(Text)
    file_path = Column(String(512))
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="papers")
    claims = relationship("Claim", back_populates="paper", cascade="all, delete")
    chunks = relationship("Chunk", back_populates="paper", cascade="all, delete")


class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(Integer, primary_key=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    section = Column(String(64))
    content = Column(Text, nullable=False)
    embedding = Column(JSON)

    paper = relationship("Paper", back_populates="chunks")


class Claim(Base):
    __tablename__ = "claims"
    id = Column(Integer, primary_key=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    text = Column(Text, nullable=False)
    subject = Column(String(255))
    relationship_type = Column(String(128))
    claim_property = Column(String(255))
    claim_value = Column(String(128))
    comparison = Column(String(255))
    claim_type = Column(String(64))
    confidence = Column(Float, default=0.5)
    created_at = Column(DateTime, default=datetime.utcnow)

    paper = relationship("Paper", back_populates="claims")


class ResearchGap(Base):
    __tablename__ = "research_gaps"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    gap_type = Column(String(64))
    title = Column(String(512))
    description = Column(Text)
    evidence = Column(JSON)
    opportunity_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="gaps")


class Hypothesis(Base):
    __tablename__ = "hypotheses"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    gap_id = Column(Integer, ForeignKey("research_gaps.id"), nullable=True)
    text = Column(Text, nullable=False)
    null_hypothesis = Column(Text)
    independent_var = Column(Text)
    dependent_var = Column(Text)
    control_vars = Column(JSON)
    novelty_score = Column(Float, default=0.0)
    evidence_score = Column(Float, default=0.0)
    testability_score = Column(Float, default=0.0)
    feasibility_score = Column(Float, default=0.0)
    overall_score = Column(Float, default=0.0)
    evidence_chain = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="hypotheses")
class ExperimentPlan(Base):
    __tablename__ = "experiment_plans"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    hypothesis_id = Column(Integer, ForeignKey("hypotheses.id"), nullable=False)

    # Structured plan stored as JSON
    plan = Column(JSON)
    markdown = Column(Text)  # renderable markdown export

    created_at = Column(DateTime, default=datetime.utcnow)
