"""HTTP API for the planning engine.

Only a health check for now; the agent tools (get_requirements, audit_progress, ...)
are added in Phase 1.
"""

from fastapi import FastAPI

app = FastAPI(title="Beyond the Syllabus engine", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
