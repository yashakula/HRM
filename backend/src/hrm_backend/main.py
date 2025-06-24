from fastapi import FastAPI
from .database import create_tables

app = FastAPI(
    title="HRM Backend API",
    description="Human Resource Management System API",
    version="0.1.0"
)

@app.on_event("startup")
async def startup_event():
    """Create database tables on startup"""
    create_tables()

@app.get("/")
async def root():
    return {"message": "HRM Backend API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "configured"}