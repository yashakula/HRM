#!/usr/bin/env python3
"""
Seed Permissions Script

This script populates the permissions and role_permissions tables with initial data.
Run this script after creating the permissions tables.

Usage:
    python scripts/seed_permissions.py
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from hrm_backend.database import engine, SessionLocal
from hrm_backend.models import Permission, RolePermission, Base
from hrm_backend.permission_registry import PERMISSION_DEFINITIONS, ROLE_PERMISSIONS, validate_role_permissions
from sqlalchemy.orm import Session
from sqlalchemy import text

def create_permissions_tables():
    """Create the permissions tables using SQLAlchemy"""
    print("Creating permissions tables...")
    Base.metadata.create_all(bind=engine)
    print("Permissions tables created successfully!")

def seed_permissions(db: Session):
    """Seed the permissions table with all permission definitions"""
    print("Seeding permissions...")
    
    # Clear existing permissions (for development)
    db.query(RolePermission).delete()
    db.query(Permission).delete()
    db.commit()
    
    # Insert all permissions
    permissions_created = 0
    for name, description, resource_type, action, scope in PERMISSION_DEFINITIONS:
        permission = Permission(
            name=name,
            description=description,
            resource_type=resource_type,
            action=action,
            scope=scope
        )
        db.add(permission)
        permissions_created += 1
    
    db.commit()
    print(f"Created {permissions_created} permissions")
    
    return permissions_created

def seed_role_permissions(db: Session):
    """Seed the role_permissions table with role-permission mappings"""
    print("Seeding role-permission mappings...")
    
    # Get all permissions by name for quick lookup
    permissions = {p.name: p for p in db.query(Permission).all()}
    
    role_permissions_created = 0
    
    for role_enum, permission_names in ROLE_PERMISSIONS.items():
        print(f"  Processing role: {role_enum}")
        
        for permission_name in permission_names:
            if permission_name not in permissions:
                print(f"    WARNING: Permission '{permission_name}' not found for role '{role_enum}'")
                continue
            
            permission = permissions[permission_name]
            
            # Check if role-permission mapping already exists
            existing = db.query(RolePermission).filter(
                RolePermission.role_enum == role_enum,
                RolePermission.permission_id == permission.permission_id
            ).first()
            
            if not existing:
                role_permission = RolePermission(
                    role_enum=role_enum,
                    permission_id=permission.permission_id
                )
                db.add(role_permission)
                role_permissions_created += 1
    
    db.commit()
    print(f"Created {role_permissions_created} role-permission mappings")
    
    return role_permissions_created

def verify_seeding(db: Session):
    """Verify that seeding was successful"""
    print("\nVerifying seeded data...")
    
    # Count permissions
    permission_count = db.query(Permission).count()
    print(f"Total permissions: {permission_count}")
    
    # Count role-permission mappings
    role_permission_count = db.query(RolePermission).count()
    print(f"Total role-permission mappings: {role_permission_count}")
    
    # Show permissions by role
    for role_enum in ["HR_ADMIN", "SUPERVISOR", "EMPLOYEE"]:
        count = db.query(RolePermission).filter(RolePermission.role_enum == role_enum).count()
        print(f"  {role_enum}: {count} permissions")
    
    # Show some sample permissions
    print("\nSample permissions:")
    sample_permissions = db.query(Permission).limit(5).all()
    for perm in sample_permissions:
        print(f"  {perm.name}: {perm.description}")
    
    return permission_count, role_permission_count

def main():
    """Main function to run the seeding process"""
    print("Starting permissions seeding process...")
    
    # Validate permission registry first
    if not validate_role_permissions():
        print("ERROR: Permission registry validation failed!")
        sys.exit(1)
    
    print("Permission registry validation passed!")
    
    # Create tables
    create_permissions_tables()
    
    # Seed data
    db = SessionLocal()
    try:
        permissions_count = seed_permissions(db)
        role_permissions_count = seed_role_permissions(db)
        
        # Verify seeding
        verify_seeding(db)
        
        print(f"\n✅ Seeding completed successfully!")
        print(f"   - {permissions_count} permissions created")
        print(f"   - {role_permissions_count} role-permission mappings created")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()