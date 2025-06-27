from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import create_tables, get_db
from .routers import employees, auth, departments, assignment_types, assignments
from .seed_data import create_all_seed_data
import os
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="HRM Backend API",
    description="Human Resource Management System API",
    version="0.1.0"
)

# Environment-aware CORS configuration
def get_cors_origins():
    """Get CORS origins from environment or use defaults"""
    cors_origins_env = os.getenv("BACKEND_CORS_ORIGINS", "")
    
    # Default localhost origins for development
    default_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000", 
        "http://0.0.0.0:3000",
    ]
    
    if cors_origins_env:
        # Split environment variable by comma and add to defaults
        env_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
        return default_origins + env_origins
    
    return default_origins

# Add CORS middleware with environment-aware origins
cors_origins = get_cors_origins()
logger.info(f"CORS origins configured: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=[
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "Cookie",
        "Set-Cookie",
    ],
    expose_headers=["Set-Cookie"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(employees.router, prefix="/api/v1")
app.include_router(departments.router, prefix="/api/v1")
app.include_router(assignment_types.router, prefix="/api/v1")
app.include_router(assignments.router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Create database tables and seed data on startup"""
    create_tables()
    
    # Create seed data if enabled (default: True in development)
    create_seed = os.getenv("CREATE_SEED_DATA", "true").lower() == "true"
    
    if create_seed:
        try:
            # Get database session
            db = next(get_db())
            result = create_all_seed_data(db)
            
            if result["success"]:
                logger.info(f"Seed data initialization: {result['message']}")
            else:
                logger.error(f"Seed data initialization failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error during seed data initialization: {str(e)}")
        finally:
            if 'db' in locals():
                db.close()
    else:
        logger.info("Seed data creation disabled (CREATE_SEED_DATA=false)")

@app.get("/")
async def root():
    return {"message": "HRM Backend API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "configured"}

