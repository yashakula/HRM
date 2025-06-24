from fastapi import FastAPI
from .database import create_tables
from .routers import employees, auth

app = FastAPI(
    title="HRM Backend API",
    description="Human Resource Management System API",
    version="0.1.0"
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(employees.router, prefix="/api/v1")

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