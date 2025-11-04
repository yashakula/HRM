#!/usr/bin/env python3
"""
Seed roles into the database.
Creates the four core roles: SUPER_USER, HR_ADMIN, SUPERVISOR, EMPLOYEE
"""

import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from hrm_backend.database import get_database_url
from hrm_backend.models import Base, Role

def seed_roles():
    """Create the four core roles if they don't exist"""
    # Connect to database
    DATABASE_URL = get_database_url()
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        print("Seeding roles...")

        # Define the four core roles
        roles = [
            {"name": "SUPER_USER", "description": "Super user with full system access"},
            {"name": "HR_ADMIN", "description": "HR administrator with employee management access"},
            {"name": "SUPERVISOR", "description": "Supervisor with team management access"},
            {"name": "EMPLOYEE", "description": "Regular employee with basic access"}
        ]

        created_count = 0
        for role_data in roles:
            # Check if role already exists
            existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
            if not existing_role:
                role = Role(
                    name=role_data["name"],
                    description=role_data["description"]
                )
                db.add(role)
                created_count += 1
                print(f"  Created role: {role_data['name']}")
            else:
                print(f"  Role already exists: {role_data['name']}")

        db.commit()
        print(f"\n✅ Successfully seeded {created_count} new roles")
        print(f"   Total roles in database: {db.query(Role).count()}")

    except Exception as e:
        print(f"\n❌ Error seeding roles: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    seed_roles()
