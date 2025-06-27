# Cloudflare Tunnel Deployment Guide

This guide explains how to deploy the HRM system using Cloudflare tunnels with Docker, including proper cookie authentication configuration.

## Prerequisites

1. **Cloudflare Account** with a domain (or use free trycloudflare.com subdomain)
2. **Docker** and **Docker Compose** installed
3. **Cloudflare CLI** (cloudflared) - optional for setup, not required for deployment

## Quick Start

### 1. Get Tunnel Token

#### Option A: Using Cloudflare Dashboard (Recommended)
1. Go to [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/)
2. Navigate to **Access** → **Tunnels**
3. Click **Create a tunnel**
4. Choose **Cloudflared** connector
5. Name your tunnel (e.g., "hrm-system")
6. Save the tunnel token (starts with `eyJ...`)

#### Option B: Using cloudflared CLI
```bash
# Install cloudflared
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# Login and create tunnel
cloudflared tunnel login
cloudflared tunnel create hrm-system
cloudflared tunnel token hrm-system
```

### 2. Configure Environment

Edit `deployment/.env.tunnel`:

```bash
# Cloudflare Tunnel Configuration
CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoiYWJjZGVmZ2hpams...your-actual-token-here
TUNNEL_DOMAIN=your-tunnel-name.trycloudflare.com

# Update API URLs
NEXT_PUBLIC_API_URL=https://your-tunnel-name.trycloudflare.com

# Update CORS Origins  
BACKEND_CORS_ORIGINS=https://your-tunnel-name.trycloudflare.com,https://*.trycloudflare.com

# Cookie Domain (for custom domains)
COOKIE_DOMAIN=.your-custom-domain.com
```

### 3. Start Tunnel Deployment

```bash
# Start all services with tunnel
./deployment/run_containers.sh start --env tunnel

# Check status
./deployment/run_containers.sh status --env tunnel

# View logs (to see tunnel URL if using trycloudflare.com)
./deployment/run_containers.sh logs --env tunnel
```

## Cookie Authentication Configuration

### The Cookie Problem with Tunnels

Cloudflare tunnels create cross-origin scenarios that break default cookie settings:

1. **Domain Mismatch**: `localhost` cookies don't work with `*.trycloudflare.com` domains
2. **HTTPS Requirement**: Tunnels use HTTPS, requiring `secure=true` cookies
3. **SameSite Restrictions**: Cross-origin requests need `samesite=none`

### Our Solution

The system automatically configures cookies based on environment:

```python
# Development (localhost)
cookie_config = {
    "httponly": True,
    "secure": False,      # HTTP allowed
    "samesite": "lax"     # Same-origin only
}

# Tunnel Mode
cookie_config = {
    "httponly": True,
    "secure": True,       # HTTPS required
    "samesite": "none",   # Cross-origin allowed
    "domain": ".trycloudflare.com"  # Domain-wide cookies
}
```

### Environment Variables

| Variable | Development | Tunnel | Description |
|----------|-------------|---------|-------------|
| `COOKIE_SECURE` | `false` | `true` | Require HTTPS for cookies |
| `COOKIE_SAMESITE` | `lax` | `none` | Cross-origin cookie policy |
| `COOKIE_DOMAIN` | `null` | `.trycloudflare.com` | Cookie domain scope |
| `TUNNEL_MODE` | `false` | `true` | Enable tunnel-specific settings |

## Tunnel Routing Configuration

### For trycloudflare.com (Free)

No additional routing needed - cloudflared automatically creates a random subdomain.

### For Custom Domains

Add DNS record in Cloudflare:
```
Type: CNAME
Name: hrm (or subdomain of choice)
Content: your-tunnel-uuid.cfargotunnel.com
```

Update tunnel configuration:
```bash
# In .env.tunnel
TUNNEL_DOMAIN=hrm.yourdomain.com
NEXT_PUBLIC_API_URL=https://hrm.yourdomain.com
BACKEND_CORS_ORIGINS=https://hrm.yourdomain.com
COOKIE_DOMAIN=.yourdomain.com
```

## Security Configuration

### CORS Settings

The backend automatically configures CORS for tunnel domains:

```python
# Environment-based CORS
BACKEND_CORS_ORIGINS=https://your-tunnel.trycloudflare.com,https://*.trycloudflare.com
```

### Production Security

For production deployments:

1. **Use Custom Domain**: Avoid `*.trycloudflare.com` for production
2. **Secure Passwords**: Update database passwords in `.env.tunnel`
3. **SSL Certificates**: Cloudflare handles SSL automatically
4. **Access Control**: Consider Cloudflare Access policies

## Troubleshooting

### 1. Tunnel Not Starting

```bash
# Check tunnel token
./deployment/run_containers.sh logs --env tunnel

# Common errors:
# - Invalid token format
# - Expired token
# - Network connectivity issues
```

### 2. Authentication Failures

```bash
# Check cookie configuration
docker-compose -f docker-compose.yml -f docker-compose.tunnel.yml exec backend env | grep COOKIE

# Verify browser cookies
# - Open browser dev tools
# - Check Application → Cookies
# - Look for session_token with correct domain/secure flags
```

### 3. CORS Errors

```bash
# Verify CORS origins
docker-compose -f docker-compose.yml -f docker-compose.tunnel.yml exec backend env | grep CORS

# Check tunnel domain matches CORS configuration
```

### 4. Database Connection Issues

```bash
# Database is internal-only in tunnel mode
# Access via docker exec:
docker-compose -f docker-compose.yml -f docker-compose.tunnel.yml exec database psql -U postgres hrms
```

## Advanced Configuration

### Custom Tunnel Config File

For advanced routing, create `tunnel-config.yml`:

```yaml
tunnel: your-tunnel-uuid
credentials-file: /etc/cloudflared/credentials.json

ingress:
  - hostname: hrm.yourdomain.com
    service: http://frontend:3000
  - service: http_status:404
```

Mount in docker-compose:
```yaml
cloudflare-tunnel:
  volumes:
    - ./tunnel-config.yml:/etc/cloudflared/config.yml:ro
```

### Multiple Environments

You can run multiple tunnel environments:

```bash
# Development tunnel
cp .env.tunnel .env.tunnel-dev
# Edit .env.tunnel-dev with dev-specific settings

# Production tunnel  
cp .env.tunnel .env.tunnel-prod
# Edit .env.tunnel-prod with prod-specific settings
```

## Login Credentials

Default test accounts work the same in tunnel mode:
- **HR Admin**: `hr_admin` / `admin123`
- **Supervisor**: `supervisor1` / `super123`  
- **Employee**: `employee1` / `emp123`

## Monitoring and Maintenance

### Check Tunnel Status
```bash
./deployment/run_containers.sh status --env tunnel
```

### View Tunnel Logs
```bash
./deployment/run_containers.sh logs --env tunnel
```

### Restart Tunnel
```bash
./deployment/run_containers.sh restart --env tunnel
```

## Production Checklist

- [ ] Custom domain configured
- [ ] Secure database password set
- [ ] CORS origins properly configured
- [ ] Cookie domain matches your domain
- [ ] Tunnel token secured (not in public repos)
- [ ] Cloudflare Access policies configured (optional)
- [ ] Monitoring and alerting set up
- [ ] Backup strategy implemented