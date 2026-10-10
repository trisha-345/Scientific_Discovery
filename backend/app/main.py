import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.config import settings
from app.routers import projects, papers, analysis, dashboard, experiments

app = FastAPI(title=settings.APP_NAME)

# ALLOWED_ORIGINS is a comma-separated list, e.g. "https://myapp.vercel.app,http://localhost:5173"
allowed = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000")
origins = [o.strip() for o in allowed.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

app.include_router(projects.router)
app.include_router(papers.router)
app.include_router(analysis.router)
app.include_router(dashboard.router)
app.include_router(experiments.router)


@app.get("/")
def root():
    return {"status": "ok", "app": settings.APP_NAME}
