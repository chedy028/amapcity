"""
Cable Ampacity Design Assistant - FastAPI Backend

Main entry point for the API server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import calculations, chat, reports

app = FastAPI(
    title="Cable Ampacity Design Assistant",
    description="LLM-powered cable ampacity calculator with engineering report generation",
    version="0.1.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "https://ampacity-app.loca.lt",
        "https://ampacity-api.loca.lt",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(calculations.router, prefix="/api", tags=["calculations"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(reports.router, prefix="/api", tags=["reports"])


@app.get("/")
async def root():
    return {
        "name": "Cable Ampacity Design Assistant",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/api/health")
async def health():
    return {"status": "healthy"}
