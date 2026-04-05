"""
Sherlock — Autonomous Data Scientist.

FastAPI application entry point.
"""

from fastapi import FastAPI


app = FastAPI(
    title="Sherlock",
    description="Autonomous Data Scientist",
    version="0.1.0"
)




@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "sherlock",
        "status": "operational",
        "version": "0.1.0",
    }


@app.get("/health")
async def health():
    """Health-check endpoint."""
    return {"status": "ok"}
