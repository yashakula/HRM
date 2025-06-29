#!/usr/bin/env python3
"""
Migration script to transition leave requests from assignment-based to employee-based.

This script:
1. Adds employee_id column to leave_request table
2. Migrates data from assignment_id to employee_id
3. Removes assignment_id column
4. Updates constraints and indexes
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from hrm_backend.database import get_database_url
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the migration to convert leave requests from assignment-based to employee-based"""
    
    # Get database connection
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    with engine.connect() as connection:
        # Start transaction
        trans = connection.begin()
        
        try:
            logger.info("Starting leave request migration...")
            
            # Step 1: Add employee_id column (nullable initially)
            logger.info("Step 1: Adding employee_id column to leave_request table")
            connection.execute(text("""
                ALTER TABLE leave_request 
                ADD COLUMN employee_id INTEGER
            """))
            
            # Step 2: Populate employee_id from assignment relationships
            logger.info("Step 2: Populating employee_id from assignment relationships")
            result = connection.execute(text("""
                UPDATE leave_request 
                SET employee_id = (
                    SELECT a.employee_id 
                    FROM assignment a 
                    WHERE a.assignment_id = leave_request.assignment_id
                )
            """))
            logger.info(f"Updated {result.rowcount} leave request records")
            
            # Step 3: Verify all records were updated
            logger.info("Step 3: Verifying data integrity")
            null_count = connection.execute(text("""
                SELECT COUNT(*) as count 
                FROM leave_request 
                WHERE employee_id IS NULL
            """)).fetchone()
            
            if null_count.count > 0:
                raise Exception(f"Migration failed: {null_count.count} records have NULL employee_id")
            
            # Step 4: Make employee_id NOT NULL and add foreign key constraint
            logger.info("Step 4: Adding constraints to employee_id column")
            connection.execute(text("""
                ALTER TABLE leave_request 
                ALTER COLUMN employee_id SET NOT NULL
            """))
            
            connection.execute(text("""
                ALTER TABLE leave_request 
                ADD CONSTRAINT fk_leave_request_employee 
                FOREIGN KEY (employee_id) REFERENCES employee(employee_id)
            """))
            
            # Step 5: Create index for performance
            logger.info("Step 5: Creating index on employee_id")
            connection.execute(text("""
                CREATE INDEX idx_leave_request_employee_id 
                ON leave_request(employee_id)
            """))
            
            # Step 6: Drop old assignment_id foreign key constraint
            logger.info("Step 6: Dropping old assignment_id foreign key constraint")
            connection.execute(text("""
                ALTER TABLE leave_request 
                DROP CONSTRAINT leave_request_assignment_id_fkey
            """))
            
            # Step 7: Drop assignment_id column
            logger.info("Step 7: Dropping assignment_id column")
            connection.execute(text("""
                ALTER TABLE leave_request 
                DROP COLUMN assignment_id
            """))
            
            # Step 8: Verify final structure
            logger.info("Step 8: Verifying final table structure")
            result = connection.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'leave_request' 
                ORDER BY ordinal_position
            """))
            
            logger.info("Final leave_request table structure:")
            for row in result:
                logger.info(f"  {row.column_name}: {row.data_type} ({'NULL' if row.is_nullable == 'YES' else 'NOT NULL'})")
            
            # Commit transaction
            trans.commit()
            logger.info("Migration completed successfully!")
            
        except Exception as e:
            # Rollback on error
            trans.rollback()
            logger.error(f"Migration failed: {e}")
            raise

def rollback_migration():
    """Rollback the migration (for testing purposes)"""
    
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    with engine.connect() as connection:
        trans = connection.begin()
        
        try:
            logger.info("Starting migration rollback...")
            
            # Add assignment_id column back
            logger.info("Adding assignment_id column back")
            connection.execute(text("""
                ALTER TABLE leave_request 
                ADD COLUMN assignment_id INTEGER
            """))
            
            # This rollback is incomplete - we would need to map employees back to assignments
            # For safety, we'll just warn about this
            logger.warning("ROLLBACK INCOMPLETE: assignment_id column added but data not restored")
            logger.warning("Manual intervention required to restore assignment relationships")
            
            trans.commit()
            logger.info("Partial rollback completed")
            
        except Exception as e:
            trans.rollback()
            logger.error(f"Rollback failed: {e}")
            raise

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_migration()
    else:
        run_migration()