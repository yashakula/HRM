-- Migration Script: Create Permissions Tables
-- This script creates the permissions and role_permissions tables for the Enhanced Permission System

-- Create permissions table
CREATE TABLE IF NOT EXISTS permissions (
    permission_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    resource_type VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    scope VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_permissions_name ON permissions(name);
CREATE INDEX IF NOT EXISTS idx_permissions_resource_action ON permissions(resource_type, action);
CREATE INDEX IF NOT EXISTS idx_permissions_resource_type ON permissions(resource_type);

-- Add constraints
ALTER TABLE permissions 
ADD CONSTRAINT chk_permissions_name_format 
CHECK (name ~ '^[a-z_]+\.[a-z_]+(\.[a-z_]+)?$');

ALTER TABLE permissions 
ADD CONSTRAINT chk_permissions_resource_type 
CHECK (resource_type IN ('employee', 'assignment', 'leave_request', 'department', 'assignment_type', 'user', 'attendance', 'compensation'));

ALTER TABLE permissions 
ADD CONSTRAINT chk_permissions_action 
CHECK (action IN ('create', 'read', 'update', 'delete', 'approve', 'reject', 'search', 'deactivate', 'manage', 'manage_supervisors', 'log'));

ALTER TABLE permissions 
ADD CONSTRAINT chk_permissions_scope 
CHECK (scope IS NULL OR scope IN ('own', 'supervised', 'all'));

-- Create role_permissions table
CREATE TABLE IF NOT EXISTS role_permissions (
    role_enum VARCHAR(20) NOT NULL,
    permission_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (role_enum, permission_id),
    FOREIGN KEY (permission_id) REFERENCES permissions(permission_id) ON DELETE CASCADE
);

-- Add constraint for valid role enum values
ALTER TABLE role_permissions 
ADD CONSTRAINT chk_role_permissions_role_enum 
CHECK (role_enum IN ('HR_ADMIN', 'SUPERVISOR', 'EMPLOYEE'));

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_role_permissions_role ON role_permissions(role_enum);
CREATE INDEX IF NOT EXISTS idx_role_permissions_permission ON role_permissions(permission_id);

-- Grant necessary permissions (if using specific database users)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON permissions TO hrm_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON role_permissions TO hrm_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE permissions_permission_id_seq TO hrm_app_user;

-- Verify tables were created successfully
\echo 'Permissions tables created successfully!'
\echo 'Checking table structure...'

\d permissions;
\d role_permissions;

-- Show table counts (should be 0 initially)
SELECT 'permissions' as table_name, COUNT(*) as row_count FROM permissions
UNION ALL
SELECT 'role_permissions' as table_name, COUNT(*) as row_count FROM role_permissions;