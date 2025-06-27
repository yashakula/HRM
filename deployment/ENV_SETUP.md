# Environment Configuration Setup

## Overview
This project uses environment-specific configuration files that are **NOT tracked in git** for security reasons. You must create your own environment files from the provided templates.

## Security Notice
**🔒 IMPORTANT: Environment files contain sensitive data (passwords, tokens, API keys) and should NEVER be committed to git.**

## Setup Instructions

### 1. Development Environment
```bash
# Copy template to create development environment file
cp .env.development.template .env.development

# Edit the file if needed (default values work for development)
nano .env.development
```

### 2. Production Environment
```bash
# Copy template to create production environment file
cp .env.production.template .env.production

# IMPORTANT: Edit with secure values for production
nano .env.production
```

**Required Production Changes:**
- Replace `your_secure_database_password_here` with a strong password
- Update `yourdomain.com` with your actual domain
- Add proper SSL certificate paths if using HTTPS
- Generate a secure session secret

### 3. Tunnel Environment (Optional)
```bash
# Copy template to create tunnel environment file
cp .env.tunnel.template .env.tunnel

# Edit with your Cloudflare tunnel configuration
nano .env.tunnel
```

**Required Tunnel Setup:**
- Get tunnel token from Cloudflare dashboard
- Replace `your_tunnel_token_here` with actual token
- Update `your_domain.com` with your tunnel domain

## File Structure
```
deployment/
├── .env.development.template    # Development template (safe to commit)
├── .env.production.template     # Production template (safe to commit)
├── .env.tunnel.template         # Tunnel template (safe to commit)
├── .env.development             # Your dev config (DO NOT COMMIT)
├── .env.production              # Your prod config (DO NOT COMMIT)
└── .env.tunnel                  # Your tunnel config (DO NOT COMMIT)
```

## Usage with Deployment Script
```bash
# Development environment
./run_containers.sh start --env dev

# Production environment
./run_containers.sh start --env prod

# Tunnel environment
./run_containers.sh start --env tunnel
```

## Security Best Practices

### ✅ DO:
- Use the template files as starting points
- Generate strong, unique passwords for production
- Keep actual environment files out of version control
- Regularly rotate sensitive credentials
- Use environment-specific configurations

### ❌ DON'T:
- Commit actual environment files to git
- Use default passwords in production
- Share environment files via email or chat
- Include sensitive data in commit messages
- Use production credentials in development

## Troubleshooting

### "Environment file not found" Error
If you get an error about missing environment files:
1. Check that you've copied the template files
2. Verify the file names match exactly (`.env.development`, `.env.production`, `.env.tunnel`)
3. Ensure files are in the `deployment/` directory

### "Permission denied" Error
If you can't read environment files:
```bash
# Fix file permissions
chmod 600 .env.*
```

### Git Tracking Issues
If git tries to track environment files:
```bash
# Remove from git tracking
git rm --cached .env.development .env.production .env.tunnel

# Verify .gitignore includes environment files
cat ../.gitignore | grep -E "\.env"
```

## Additional Security

For production deployments, consider:
- Using a secrets management service (AWS Secrets Manager, HashiCorp Vault, etc.)
- Implementing environment variable injection at deployment time
- Using encrypted environment variable storage
- Setting up proper backup and rotation policies for secrets