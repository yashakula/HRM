#!/usr/bin/env python3
"""
Wrapper script to run database seeding in Docker container.
This script runs the actual seeding script inside the backend container.
"""

import subprocess
import sys
import os

def run_in_container(command):
    """Run a command in the backend Docker container"""
    docker_cmd = [
        "docker-compose", "exec", "-T", "backend", 
        "uv", "run", "python", "scripts/seed_database.py", command
    ]
    
    try:
        result = subprocess.run(docker_cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}", file=sys.stderr)
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return False
    except FileNotFoundError:
        print("❌ Docker Compose not found. Make sure Docker is installed and running.", file=sys.stderr)
        return False

def check_containers():
    """Check if containers are running"""
    try:
        result = subprocess.run(
            ["docker-compose", "ps", "--services", "--filter", "status=running"],
            check=True, capture_output=True, text=True
        )
        running_services = result.stdout.strip().split('\n')
        
        if 'backend' not in running_services:
            print("❌ Backend container is not running.")
            print("Start containers with: docker-compose up -d")
            return False
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to check container status.")
        print("Make sure Docker Compose is available and run: docker-compose up -d")
        return False

def show_help():
    """Show usage information"""
    print("""
HRM Database Seeding Tool
========================

Usage:
  python seed_db.py [command]

Commands:
  seed      Create seed data (if not exists)
  reset     Delete and recreate all seed data
  help      Show this help message

This tool runs the seeding script inside the Docker backend container.

Requirements:
  - Docker and Docker Compose must be installed
  - Containers must be running: docker-compose up -d

Seed Data Includes:
  👥 3 Users: hr_admin, supervisor1, employee1
  🏢 5 Departments: Engineering, Marketing, HR, Finance, Operations  
  👔 15 Assignment Types: Various roles across departments
  👤 5 Employees: Sample employee profiles
  📋 5 Assignments: Employee-role mappings with supervisors

Login Credentials:
  HR Admin:    hr_admin / admin123
  Supervisor:  supervisor1 / super123  
  Employee:    employee1 / emp123
""")

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        command = "help"
    else:
        command = sys.argv[1].lower()
    
    if command in ["help", "-h", "--help"]:
        show_help()
        return
    
    if command not in ["seed", "reset"]:
        print(f"❌ Unknown command: {command}")
        show_help()
        return
    
    # Check if containers are running
    if not check_containers():
        return
    
    # Run the command in the container
    print(f"Running '{command}' command in Docker container...")
    success = run_in_container(command)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()