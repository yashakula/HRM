from fastapi import FastAPI
from .database import create_tables, get_db
from .routers import employees, auth
from .seed_data import create_all_seed_data
import os
import logging

logger = logging.getLogger(__name__)

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

@app.post("/admin/seed-data")
async def create_seed_data_endpoint():
    """Manually trigger seed data creation (for testing/setup)"""
    try:
        db = next(get_db())
        result = create_all_seed_data(db)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        if 'db' in locals():
            db.close()

@app.post("/admin/reset-seed-data")
async def reset_seed_data_endpoint():
    """Reset seed data (for testing)"""
    try:
        from .seed_data import reset_seed_data
        db = next(get_db())
        result = reset_seed_data(db)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        if 'db' in locals():
            db.close()