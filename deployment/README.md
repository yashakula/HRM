# HRM Multi-Environment Deployment

This directory contains scripts and configuration for deploying the HRM system in different environments.

## Overview

The HRM system supports multiple deployment environments with different security configurations:

- **Development (`dev`)**: All services exposed for direct access and debugging
- **Production (`prod`)**: Only frontend exposed, backend and database secured internally
- **Tunnel (`tunnel`)**: Cloudflare tunnel deployment for secure external access

## File Structure

```
deployment/
├── run_containers.sh           # Main deployment script with environment support
├── docker-compose.yml          # Base configuration (shared)
├── docker-compose.dev.yml      # Development overrides
├── docker-compose.prod.yml     # Production overrides
├── docker-compose.tunnel.yml   # Cloudflare tunnel overrides
├── .env.development.template   # Development environment template
├── .env.production.template    # Production environment template
├── .env.tunnel.template        # Tunnel environment template
├── .env.development            # Development environment variables (local only)
├── .env.production             # Production environment variables (local only)
├── .env.tunnel                 # Tunnel environment variables (local only)
├── ENV_SETUP.md               # Environment setup and security guide
├── TUNNEL_SETUP.md            # Cloudflare tunnel setup guide
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

### Tunnel Environment (Cloudflare)
```bash
# Start tunnel environment
./deployment/run_containers.sh start --env tunnel

# Accessible via Cloudflare tunnel:
# - Frontend: https://yashakula.com (or your domain)
# - Backend/Database: Internal access only
# - No local ports exposed (secure tunnel access only)
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

### Tunnel Mode
- **Ports Exposed**: None (all traffic via Cloudflare tunnel)
- **Volume Mounts**: None (uses built images)
- **Security**: Cloudflare tunnel encryption, environment-aware cookies
- **Use Case**: Secure external access, production deployment with tunnel

## Available Commands

```bash
# Environment Management
./deployment/run_containers.sh start [--env dev|prod|tunnel]     # Start containers
./deployment/run_containers.sh stop [--env dev|prod|tunnel]      # Stop containers  
./deployment/run_containers.sh restart [--env dev|prod|tunnel]   # Restart containers
./deployment/run_containers.sh rebuild [--env dev|prod|tunnel]   # Rebuild and start

# Monitoring
./deployment/run_containers.sh status [--env dev|prod|tunnel]    # Show container status
./deployment/run_containers.sh logs [--env dev|prod|tunnel]      # Show container logs

# Database Management
./deployment/run_containers.sh seed [--env dev|prod|tunnel]      # Seed database
./deployment/run_containers.sh reset [--env dev|prod|tunnel]     # Reset and reseed database

# Cleanup
./deployment/run_containers.sh clean [--env dev|prod|tunnel]     # Remove containers/volumes
```

## Environment Variables

**🔒 SECURITY NOTE**: Environment files (`.env.*`) are not tracked in git. Use template files to create your environment configurations. See `ENV_SETUP.md` for detailed setup instructions.

### Development (.env.development)
- `NEXT_PUBLIC_API_URL=http://localhost:8000` - Frontend API URL
- `POSTGRES_PASSWORD=mysecretpassword` - Database password
- `CREATE_SEED_DATA=true` - Enable test data creation
- `NODE_ENV=development` - Development mode

### Production (.env.production)
- `NEXT_PUBLIC_API_URL=http://backend:8000` - Internal API URL (for local testing)
- `POSTGRES_PASSWORD=your_secure_password` - Database password (use secure password)
- `CREATE_SEED_DATA=false` - Disable test data creation
- `NODE_ENV=production` - Production mode

### Tunnel (.env.tunnel)
- `NEXT_PUBLIC_API_URL=https://yashakula.com` - Tunnel domain URL
- `CLOUDFLARE_TUNNEL_TOKEN=your_token` - Cloudflare tunnel token
- `TUNNEL_DOMAIN=yashakula.com` - Your tunnel domain
- `COOKIE_SECURE=true` - Secure cookies for HTTPS
- `COOKIE_DOMAIN=.yashakula.com` - Cookie domain scope
- `BACKEND_CORS_ORIGINS=https://yashakula.com` - CORS configuration

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

### Tunnel Environment
- ✅ No local ports exposed (maximum security)
- ✅ All traffic encrypted via Cloudflare tunnel
- ✅ Environment-aware cookie security (secure, samesite)
- ✅ Automatic HTTPS with Cloudflare SSL
- ✅ Database and backend isolated to internal network
- ✅ Production-grade security configuration

## Deployment Setup

### First-Time Setup
1. **Create environment files from templates**:
   ```bash
   # Copy templates to create working environment files
   cp .env.development.template .env.development
   cp .env.production.template .env.production  
   cp .env.tunnel.template .env.tunnel
   
   # Edit files with your specific configuration
   # See ENV_SETUP.md for detailed instructions
   ```

### Production Deployment
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

### Tunnel Deployment
For Cloudflare tunnel deployment:

1. **Set up Cloudflare tunnel**:
   - See `TUNNEL_SETUP.md` for complete setup guide
   - Get tunnel token from Cloudflare dashboard
   - Configure tunnel domain in Cloudflare

2. **Update .env.tunnel**:
   ```bash
   # Set your tunnel token (keep secure!)
   CLOUDFLARE_TUNNEL_TOKEN=your_actual_tunnel_token
   
   # Set your tunnel domain
   TUNNEL_DOMAIN=yourdomain.com
   NEXT_PUBLIC_API_URL=https://yourdomain.com
   BACKEND_CORS_ORIGINS=https://yourdomain.com
   COOKIE_DOMAIN=.yourdomain.com
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

### Can't access database directly in production/tunnel
This is by design for security. To access database in production or tunnel modes:
```bash
# Production mode
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec database psql -U postgres hrms

# Tunnel mode  
docker-compose -f docker-compose.yml -f docker-compose.tunnel.yml exec database psql -U postgres hrms
```

### Tunnel not connecting
If Cloudflare tunnel fails to connect:
1. Verify tunnel token is correct in `.env.tunnel`
2. Check tunnel status in Cloudflare dashboard
3. Ensure tunnel domain is properly configured
4. Check container logs: `./deployment/run_containers.sh logs --env tunnel`

## Login Credentials

Default test accounts (when seeded):
- **HR Admin**: `hr_admin` / `admin123`
- **Supervisor**: `supervisor1` / `super123`
- **Employee**: `employee1` / `emp123`