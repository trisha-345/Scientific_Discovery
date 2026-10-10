import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.config import settings
from app.routers import projects, papers, analysis, dashboard, experiments

app = FastAPI(title=settings.APP_NAME)

# Read allowed origins from env var, comma-separated.
# Falls back to localhost for local development.
allowed_origins_str = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
)
allowed_origins = [o.strip() for o in allowed_origins_str.split(",") if o.strip()]

print(f"[CORS] Allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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