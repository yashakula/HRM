# HRM Multi-Environment Deployment

This directory contains scripts and configuration for deploying the HRM system in different environments.

## Overview

The HRM system supports multiple deployment environments with different security configurations:

- **Development (`dev`)**: All services exposed for direct access and debugging
- **Production (`prod`)**: Only frontend exposed, backend and database secured internally

## File Structure

```
deployment/
├── run_containers.sh           # Main deployment script with environment support
├── docker-compose.yml          # Base configuration (shared)
├── docker-compose.dev.yml      # Development overrides
├── docker-compose.prod.yml     # Production overrides
├── .env.development            # Development environment variables
├── .env.production             # Production environment variables
└── README.md                   # This documentation

Project structure:
├── backend/                    # FastAPI backend source code
├── frontend/                   # Next.js frontend source code
└── deployment/                 # All deployment configuration files
```

## Quick Start

### Development Environment (Default)
```bash
# Start development environment (default)
./deployment/run_containers.sh start
./deployment/run_containers.sh start --env dev

# All services accessible:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000  
# - Database: localhost:5432
```

### Production Environment
```bash
# Start production environment
./deployment/run_containers.sh start --env prod

# Only frontend accessible:
# - Frontend: http://localhost:3000
# - Backend/Database: Internal access only
```

## Environment Configurations

### Development Mode
- **Ports Exposed**: Frontend (3000), Backend (8000), Database (5432)
- **Volume Mounts**: Source code mounted for live reloading
- **Security**: Permissive CORS, all services accessible
- **Use Case**: Local development, testing, debugging

### Production Mode  
- **Ports Exposed**: Frontend (3000) only
- **Volume Mounts**: None (uses built images)
- **Security**: Restricted CORS, internal networking only
- **Use Case**: Production deployment, staging environments

## Available Commands

```bash
# Environment Management
./deployment/run_containers.sh start [--env dev|prod]     # Start containers
./deployment/run_containers.sh stop [--env dev|prod]      # Stop containers  
./deployment/run_containers.sh restart [--env dev|prod]   # Restart containers
./deployment/run_containers.sh rebuild [--env dev|prod]   # Rebuild and start

# Monitoring
./deployment/run_containers.sh status [--env dev|prod]    # Show container status
./deployment/run_containers.sh logs [--env dev|prod]      # Show container logs

# Database Management
./deployment/run_containers.sh seed [--env dev|prod]      # Seed database
./deployment/run_containers.sh reset [--env dev|prod]     # Reset and reseed database

# Cleanup
./deployment/run_containers.sh clean [--env dev|prod]     # Remove containers/volumes
```

## Environment Variables

### Development (.env.development)
- `NEXT_PUBLIC_API_URL=http://localhost:8000` - Frontend API URL
- `POSTGRES_PASSWORD=mysecretpassword` - Database password
- `CREATE_SEED_DATA=true` - Enable test data creation

### Production (.env.production)
- `NEXT_PUBLIC_API_URL=http://backend:8000` - Internal API URL (for local testing)
- `POSTGRES_PASSWORD=mysecretpassword` - Database password (change in real production)
- `CREATE_SEED_DATA=false` - Disable test data creation

## Security Considerations

### Development Environment
- ✅ All services directly accessible for debugging
- ✅ Live code reloading via volume mounts
- ⚠️ Not suitable for production use

### Production Environment  
- ✅ Database not accessible from outside Docker network
- ✅ Backend not accessible from outside Docker network
- ✅ Only frontend exposed as public entry point
- ✅ No volume mounts (immutable containers)
- ✅ Resource limits configured

## Production Deployment Notes

When deploying to an actual production environment:

1. **Update .env.production**:
   ```bash
   # Change API URL to your domain
   NEXT_PUBLIC_API_URL=https://yourdomain.com
   
   # Use secure database password
   POSTGRES_PASSWORD=your_secure_password_here
   
   # Update CORS origins
   BACKEND_CORS_ORIGINS=https://yourdomain.com
   ```

2. **Consider additional security**:
   - Use HTTPS/TLS certificates
   - Add reverse proxy (nginx) for SSL termination  
   - Configure firewall rules
   - Use Docker secrets for sensitive data
   - Set up backup strategies

3. **Monitor and maintain**:
   - Set up logging aggregation
   - Configure health checks
   - Plan update strategies
   - Monitor resource usage

## Troubleshooting

### Backend not starting in production
- Check database connection with: `./deployment/run_containers.sh logs --env prod`
- Verify environment variables are loaded correctly
- Ensure database password matches in both services

### Frontend can't reach backend
- In production mode, frontend uses internal Docker networking
- Verify `NEXT_PUBLIC_API_URL` points to correct endpoint
- Check CORS configuration in backend

### Permission denied on run_containers.sh
```bash
chmod +x deployment/run_containers.sh
```

### Can't access database directly in production
This is by design for security. To access database in production:
```bash
# Use docker exec to access database internally
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec database psql -U postgres hrms
```

## Login Credentials

Default test accounts (when seeded):
- **HR Admin**: `hr_admin` / `admin123`
- **Supervisor**: `supervisor1` / `super123`
- **Employee**: `employee1` / `emp123`