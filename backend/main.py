"""Stimblue+ Dashboard API — FastAPI backend."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import companies, dashboard, config, analysis

app = FastAPI(
    title="Stimblue+ Dashboard API",
    description="Backend for the Kelp Blue strategic partnership dashboard",
    version="1.0.0",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(companies.router)
app.include_router(dashboard.router)
app.include_router(config.router)
app.include_router(analysis.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "stimblue-dashboard"}
