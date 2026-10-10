import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.database import get_db
from app import models, schemas
from app.config import settings
from app.services.pdf_parser import parse_pdf
from app.services.claim_extractor import extract_claims_from_paper
from app.services.embeddings import chunk_text, embed_texts

router = APIRouter(prefix="/api/papers", tags=["papers"])
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


# ---------- shared helper ----------
def _store_paper_with_claims(
    db: Session,
    project_id: int,
    title: str,
    abstract: str,
    full_text: str,
    file_path: str | None,
) -> dict:
    """Common logic to save a paper, extract claims, and compute embeddings."""
    paper = models.Paper(
        project_id=project_id,
        title=title,
        abstract=abstract,
        full_text=full_text,
        file_path=file_path,
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)

    # Groq claim extraction
    parsed = {
        "title": title,
        "abstract": abstract,
        "full_text": full_text,
    }
    claims = extract_claims_from_paper(parsed)
    for c in claims:
        db.add(models.Claim(
            paper_id=paper.id,
            text=c["text"],
            subject=c.get("subject"),
            relationship_type=c.get("relationship_type"),
            claim_property=c.get("claim_property"),
            claim_value=c.get("claim_value"),
            comparison=c.get("comparison"),
            claim_type=c.get("claim_type", "finding"),
            confidence=c.get("confidence", 0.6),
        ))
    db.commit()

    # Embeddings
    chunks = chunk_text(full_text)[:30]
    if chunks:
        vecs = embed_texts(chunks)
        for content, v in zip(chunks, vecs):
            db.add(models.Chunk(paper_id=paper.id, content=content, embedding=v))
        db.commit()

    return {
        "paper_id": paper.id,
        "title": paper.title,
        "claims_extracted": len(claims),
        "chunks_created": len(chunks),
    }


# ---------- PDF upload ----------
@router.post("/upload")
def upload_paper(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not db.get(models.Project, project_id):
        raise HTTPException(404, "Project not found")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDFs supported")

    dest = Path(settings.UPLOAD_DIR) / f"{project_id}_{file.filename}"
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    parsed = parse_pdf(str(dest))

    return _store_paper_with_claims(
        db=db,
        project_id=project_id,
        title=parsed["title"] or file.filename,
        abstract=parsed["abstract"] or "",
        full_text=parsed["full_text"] or "",
        file_path=str(dest),
    )


# ---------- Paste text ----------
class TextPaperInput(BaseModel):
    title: str
    text: str


@router.post("/text")
def upload_text_paper(
    project_id: int,
    payload: TextPaperInput,
    db: Session = Depends(get_db),
):
    if not db.get(models.Project, project_id):
        raise HTTPException(404, "Project not found")

    text = (payload.text or "").strip()
    if len(text) < 100:
        raise HTTPException(400, "Text too short — needs at least 100 characters")

    # Auto-extract an abstract: first 500 chars, or first paragraph
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    abstract = paragraphs[0][:500] if paragraphs else text[:500]

    return _store_paper_with_claims(
        db=db,
        project_id=project_id,
        title=payload.title.strip() or "Pasted text",
        abstract=abstract,
        full_text=text,
        file_path=None,
    )


@router.get("/{project_id}", response_model=List[schemas.PaperOut])
def list_papers(project_id: int, db: Session = Depends(get_db)):
    return db.query(models.Paper).filter_by(project_id=project_id).all()