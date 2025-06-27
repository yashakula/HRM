#!/bin/bash

# HRM Container Deployment Script
# This script manages the HRM system containers (Database, Backend, Frontend)

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to load environment variables
load_env() {
    if [ -f "deployment/.env" ]; then
        export $(cat deployment/.env | grep -v '^#' | xargs)
        print_status "Environment variables loaded from deployment/.env"
    else
        print_warning "No .env file found at deployment/.env"
    fi
}

# Function to check if docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Function to check if docker-compose is available
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose is not installed. Please install docker-compose and try again."
        exit 1
    fi
    print_success "docker-compose is available"
}

# Function to display usage
usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start       Start all HRM containers (default)"
    echo "  stop        Stop all HRM containers"
    echo "  restart     Restart all HRM containers"
    echo "  rebuild     Rebuild and start containers (includes building images)"
    echo "  logs        Show logs from all containers"
    echo "  status      Show status of all containers"
    echo "  seed        Run database seeding after containers are up"
    echo "  reset       Reset database and reseed with fresh data"
    echo "  clean       Stop containers and remove images/volumes"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Start containers"
    echo "  $0 start             # Start containers"
    echo "  $0 rebuild           # Rebuild and start containers"
    echo "  $0 seed              # Seed database with test data"
    echo "  $0 logs              # View container logs"
}

# Function to navigate to project root
navigate_to_project() {
    cd "$(dirname "$0")/.."
    print_status "Working directory: $(pwd)"
}

# Function to start containers
start_containers() {
    print_status "Starting HRM containers..."
    docker-compose up -d
    
    print_status "Waiting for containers to be ready..."
    sleep 10
    
    # Check container status
    if docker-compose ps | grep -q "Up"; then
        print_success "HRM containers are running"
        print_status "Services available at:"
        print_status "  - Frontend: http://localhost:3000"
        print_status "  - Backend API: http://localhost:8000"
        print_status "  - Database: localhost:5432"
    else
        print_error "Some containers failed to start. Check logs with: $0 logs"
        exit 1
    fi
}


# Function to stop containers
stop_containers() {
    print_status "Stopping HRM containers..."
    docker-compose down
    print_success "HRM containers stopped"
}


# Function to restart containers
restart_containers() {
    print_status "Restarting HRM containers..."
    docker-compose restart
    
    print_status "Waiting for containers to be ready..."
    sleep 10
    
    print_success "HRM containers restarted"
    print_status "Services available at:"
    print_status "  - Frontend: http://localhost:3000"
    print_status "  - Backend API: http://localhost:8000"
    print_status "  - Database: localhost:5432"
}

# Function to rebuild and start containers
rebuild_containers() {
    print_status "Rebuilding HRM containers..."
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d
    
    print_status "Waiting for containers to be ready..."
    sleep 15
    
    if docker-compose ps | grep -q "Up"; then
        print_success "HRM containers rebuilt and running"
        print_status "Services available at:"
        print_status "  - Frontend: http://localhost:3000"
        print_status "  - Backend API: http://localhost:8000"
        print_status "  - Database: localhost:5432"
    else
        print_error "Some containers failed to start after rebuild. Check logs with: $0 logs"
        exit 1
    fi
}

# Function to show logs
show_logs() {
    print_status "Showing HRM container logs..."
    docker-compose logs -f
}

# Function to show container status
show_status() {
    print_status "HRM Container Status:"
    docker-compose ps
    echo ""
    
    # Check if services are responding
    print_status "Service Health Check:"
    
    # Check database
    if docker-compose exec -T database pg_isready -U postgres > /dev/null 2>&1; then
        print_success "Database: Ready"
    else
        print_error "Database: Not responding"
    fi
    
    # Check backend
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Backend API: Ready"
    else
        print_warning "Backend API: Not responding (may still be starting)"
    fi
    
    # Check frontend
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        print_success "Frontend: Ready"
    else
        print_warning "Frontend: Not responding (may still be starting)"
    fi
}

# Function to seed database
seed_database() {
    print_status "Seeding database with test data..."
    
    # Check if containers are running
    if ! docker-compose ps | grep -q "Up"; then
        print_error "Containers are not running. Start them first with: $0 start"
        exit 1
    fi
    
    # Run seeding script
    docker-compose exec backend uv run python scripts/seed_database.py seed
    
    if [ $? -eq 0 ]; then
        print_success "Database seeded successfully"
        print_status "Test login credentials:"
        print_status "  HR Admin: hr_admin / admin123"
        print_status "  Supervisor: supervisor1 / super123"  
        print_status "  Employee: employee1 / emp123"
    else
        print_error "Database seeding failed"
        exit 1
    fi
}

# Function to reset and seed database
reset_database() {
    print_status "Resetting and reseeding database..."
    
    # Check if containers are running
    if ! docker-compose ps | grep -q "Up"; then
        print_error "Containers are not running. Start them first with: $0 start"
        exit 1
    fi
    
    # Run reset script
    docker-compose exec backend uv run python scripts/seed_database.py reset
    
    if [ $? -eq 0 ]; then
        print_success "Database reset and seeded successfully"
        print_status "Test login credentials:"
        print_status "  HR Admin: hr_admin / admin123"
        print_status "  Supervisor: supervisor1 / super123"
        print_status "  Employee: employee1 / emp123"
    else
        print_error "Database reset failed"
        exit 1
    fi
}

# Function to clean up everything
clean_containers() {
    print_warning "This will stop containers and remove images/volumes. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_status "Cleaning up HRM containers..."
        docker-compose down -v --rmi all
        print_success "HRM containers and data cleaned up"
    else
        print_status "Clean up cancelled"
    fi
}

# Main script logic
main() {
    navigate_to_project
    load_env
    check_docker
    check_docker_compose
    
    case "${1:-start}" in
        start)
            start_containers
            ;;
        stop)
            stop_containers
            ;;
        restart)
            restart_containers
            ;;
        rebuild)
            rebuild_containers
            ;;
        logs)
            show_logs
            ;;
        status)
            show_status
            ;;
        seed)
            seed_database
            ;;
        reset)
            reset_database
            ;;
        clean)
            clean_containers
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            print_error "Unknown command: $1"
            usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"