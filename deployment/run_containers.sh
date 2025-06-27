#!/bin/bash

# HRM Container Deployment Script
# This script manages the HRM system containers with environment support
# Supports development and production environments with different configurations

set -e  # Exit on any error

# Default environment
DEFAULT_ENV="dev"
ENVIRONMENT=""

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

# Function to parse environment argument
parse_environment() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            *)
                # Keep other arguments for the main command
                shift
                ;;
        esac
    done
    
    # Set default environment if not specified
    if [ -z "$ENVIRONMENT" ]; then
        ENVIRONMENT="$DEFAULT_ENV"
    fi
    
    # Validate environment
    if [[ "$ENVIRONMENT" != "dev" && "$ENVIRONMENT" != "prod" && "$ENVIRONMENT" != "tunnel" ]]; then
        print_error "Invalid environment: $ENVIRONMENT. Use 'dev', 'prod', or 'tunnel'"
        exit 1
    fi
}

# Function to load environment-specific variables
load_env() {
    local env_file=""
    
    case "$ENVIRONMENT" in
        "dev")
            env_file=".env.development"
            ;;
        "prod")
            env_file=".env.production"
            ;;
        "tunnel")
            env_file=".env.tunnel"
            ;;
    esac
    
    if [ -f "$env_file" ]; then
        # Export variables from env file
        set -a  # automatically export all variables
        source "$env_file"
        set +a  # stop automatically exporting
        print_status "Environment variables loaded from $env_file"
    else
        print_warning "No environment file found: $env_file"
        print_warning "Using default values and system environment variables"
    fi
}

# Function to get docker-compose command with environment-specific files
get_docker_compose_cmd() {
    local compose_files="-f docker-compose.yml"
    
    case "$ENVIRONMENT" in
        "dev")
            compose_files="$compose_files -f docker-compose.dev.yml"
            ;;
        "prod")
            compose_files="$compose_files -f docker-compose.prod.yml"
            ;;
        "tunnel")
            compose_files="$compose_files -f docker-compose.tunnel.yml"
            ;;
    esac
    
    echo "docker-compose $compose_files"
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
    echo "Usage: $0 [COMMAND] [OPTIONS]"
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
    echo "Options:"
    echo "  --env ENV   Specify environment: 'dev', 'prod', or 'tunnel' (default: dev)"
    echo ""
    echo "Examples:"
    echo "  $0                         # Start containers in development mode"
    echo "  $0 start                   # Start containers in development mode"
    echo "  $0 start --env dev         # Start containers in development mode"
    echo "  $0 start --env prod        # Start containers in production mode"
    echo "  $0 start --env tunnel      # Start containers with Cloudflare tunnel"
    echo "  $0 rebuild --env tunnel    # Rebuild and start with tunnel"
    echo "  $0 logs --env tunnel       # View tunnel container logs"
    echo ""
    echo "Environment Configurations:"
    echo "  dev:    Exposes database (5432) and backend (8000) ports for direct access"
    echo "          Uses .env.development configuration"
    echo "          Includes volume mounts for live code reloading"
    echo ""
    echo "  prod:   Only exposes frontend (3000) port for security"
    echo "          Uses .env.production configuration"
    echo "          No volume mounts, uses built images"
    echo ""
    echo "  tunnel: Accessible via Cloudflare tunnel only"
    echo "          Uses .env.tunnel configuration"
    echo "          Includes cloudflare-tunnel service"
    echo "          Requires CLOUDFLARE_TUNNEL_TOKEN environment variable"
}

# Function to navigate to deployment directory
navigate_to_deployment() {
    cd "$(dirname "$0")"
    print_status "Working directory: $(pwd)"
}

# Function to start containers
start_containers() {
    local compose_cmd=$(get_docker_compose_cmd)
    
    print_status "Starting HRM containers in $ENVIRONMENT environment..."
    print_status "Using: $compose_cmd"
    
    $compose_cmd up -d
    
    print_status "Waiting for containers to be ready..."
    sleep 10
    
    # Check container status
    if $compose_cmd ps | grep -q "Up"; then
        print_success "HRM containers are running in $ENVIRONMENT mode"
        print_status "Services available:"
        
        case "$ENVIRONMENT" in
            "dev")
                print_status "  - Frontend: http://localhost:3000"
                print_status "  - Backend API: http://localhost:8000"
                print_status "  - Database: localhost:5432"
                print_status ""
                print_status "Development mode: All services exposed for direct access"
                ;;
            "prod")
                print_status "  - Frontend: http://localhost:3000"
                print_status ""
                print_status "Production mode: Only frontend exposed for security"
                print_warning "Backend and database are only accessible internally"
                ;;
            "tunnel")
                print_status "  - Application: Available via Cloudflare tunnel"
                if [ -n "$TUNNEL_DOMAIN" ]; then
                    print_status "  - Tunnel URL: https://$TUNNEL_DOMAIN"
                else
                    print_warning "  - TUNNEL_DOMAIN not set, check tunnel logs for URL"
                fi
                print_status ""
                print_status "Tunnel mode: Application accessible via Cloudflare tunnel"
                print_warning "All services secured behind tunnel - no direct local access"
                ;;
        esac
    else
        print_error "Some containers failed to start. Check logs with: $0 logs --env $ENVIRONMENT"
        exit 1
    fi
}

# Function to stop containers
stop_containers() {
    local compose_cmd=$(get_docker_compose_cmd)
    
    print_status "Stopping HRM containers ($ENVIRONMENT environment)..."
    $compose_cmd down
    print_success "HRM containers stopped"
}

# Function to restart containers
restart_containers() {
    local compose_cmd=$(get_docker_compose_cmd)
    
    print_status "Restarting HRM containers ($ENVIRONMENT environment)..."
    $compose_cmd restart
    
    print_status "Waiting for containers to be ready..."
    sleep 10
    
    print_success "HRM containers restarted in $ENVIRONMENT mode"
}

# Function to rebuild and start containers
rebuild_containers() {
    local compose_cmd=$(get_docker_compose_cmd)
    
    print_status "Rebuilding HRM containers ($ENVIRONMENT environment)..."
    $compose_cmd down
    $compose_cmd build --no-cache
    $compose_cmd up -d
    
    print_status "Waiting for containers to be ready..."
    sleep 15
    
    if $compose_cmd ps | grep -q "Up"; then
        print_success "HRM containers rebuilt and running in $ENVIRONMENT mode"
    else
        print_error "Some containers failed to start after rebuild. Check logs with: $0 logs --env $ENVIRONMENT"
        exit 1
    fi
}

# Function to show logs
show_logs() {
    local compose_cmd=$(get_docker_compose_cmd)
    
    print_status "Showing HRM container logs ($ENVIRONMENT environment)..."
    $compose_cmd logs -f
}

# Function to show container status
show_status() {
    local compose_cmd=$(get_docker_compose_cmd)
    
    print_status "HRM Container Status ($ENVIRONMENT environment):"
    $compose_cmd ps
    echo ""
    
    # Check if services are responding
    print_status "Service Health Check:"
    
    # Check database (only if exposed in dev mode)
    if [ "$ENVIRONMENT" = "dev" ]; then
        if $compose_cmd exec -T database pg_isready -U postgres > /dev/null 2>&1; then
            print_success "Database: Ready (localhost:5432)"
        else
            print_error "Database: Not responding"
        fi
        
        # Check backend (only if exposed in dev mode)
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            print_success "Backend API: Ready (localhost:8000)"
        else
            print_warning "Backend API: Not responding (may still be starting)"
        fi
    else
        print_status "Database: Internal access only (production mode)"
        print_status "Backend API: Internal access only (production mode)"
    fi
    
    # Check frontend (always exposed)
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        print_success "Frontend: Ready (localhost:3000)"
    else
        print_warning "Frontend: Not responding (may still be starting)"
    fi
}

# Function to seed database
seed_database() {
    local compose_cmd=$(get_docker_compose_cmd)
    
    print_status "Seeding database with test data ($ENVIRONMENT environment)..."
    
    # Check if containers are running
    if ! $compose_cmd ps | grep -q "Up"; then
        print_error "Containers are not running. Start them first with: $0 start --env $ENVIRONMENT"
        exit 1
    fi
    
    # Run seeding script
    $compose_cmd exec backend uv run python scripts/seed_database.py seed
    
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
    local compose_cmd=$(get_docker_compose_cmd)
    
    print_status "Resetting and reseeding database ($ENVIRONMENT environment)..."
    
    # Check if containers are running
    if ! $compose_cmd ps | grep -q "Up"; then
        print_error "Containers are not running. Start them first with: $0 start --env $ENVIRONMENT"
        exit 1
    fi
    
    # Run reset script
    $compose_cmd exec backend uv run python scripts/seed_database.py reset
    
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
    local compose_cmd=$(get_docker_compose_cmd)
    
    print_warning "This will stop containers and remove images/volumes. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_status "Cleaning up HRM containers ($ENVIRONMENT environment)..."
        $compose_cmd down -v --rmi all
        print_success "HRM containers and data cleaned up"
    else
        print_status "Clean up cancelled"
    fi
}

# Main script logic
main() {
    # Store original arguments for parsing
    local original_args=("$@")
    
    # Parse environment from arguments
    parse_environment "${original_args[@]}"
    
    # Navigate to deployment directory and load environment
    navigate_to_deployment
    load_env
    check_docker
    check_docker_compose
    
    # Get the main command (first argument that's not an option)
    local command=""
    for arg in "${original_args[@]}"; do
        if [[ ! "$arg" =~ ^-- ]] && [[ "$arg" != "dev" ]] && [[ "$arg" != "prod" ]]; then
            command="$arg"
            break
        fi
    done
    
    # Default to start if no command provided
    if [ -z "$command" ]; then
        command="start"
    fi
    
    case "$command" in
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
            print_error "Unknown command: $command"
            usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"