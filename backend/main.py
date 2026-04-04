
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan"""
    print("Sherlock starting")
    print(f"   Environment : {os.getenv('ENVIRONMENT', 'unknown')}")
    print(f"   Database    : {os.getenv('POSTGRES_HOST', 'unknown')}:{os.getenv('POSTGRES_PORT', '5432')}")
    yield
    print("Sherlock shutting down")


app = FastAPI(
    title="Sherlock",
    description="Autonomous Data Scientist",
    version="0.1.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # Next.js dev server
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "sherlock",
        "status": "operational",
        "version": "0.1.0",
    }


@app.get("/health")
async def health():
    """Health-check endpoint"""
    return {"status": "ok"}
