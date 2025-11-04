from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
import os

# Database configuration
def get_database_url():
    """Get database URL from environment or default"""
    # Try to get from environment first
    db_url = os.getenv("DATABASE_URL")

    # If not set, use system user for native PostgreSQL
    if not db_url:
        import getpass
        username = getpass.getuser()
        db_url = f"postgresql://{username}@localhost:5432/hrms"

    # Expand environment variables in the URL (e.g., ${USER})
    import re
    def expand_env_var(match):
        env_var = match.group(1)
        return os.getenv(env_var, match.group(0))

    db_url = re.sub(r'\$\{(\w+)\}', expand_env_var, db_url)

    return db_url

DATABASE_URL = get_database_url()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()