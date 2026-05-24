# Deployment Guide

## Prerequisites

- **Linux server** (Ubuntu 22.04+ recommended, Debian 12, or RHEL 9 derivatives)
- **Docker** Engine 24+ and **Docker Compose** v2+
- **Domain name** pointed to your server (A record or CNAME)
- Minimum **2 GB RAM**, **10 GB** free disk space
- Open ports: **80** (HTTP) and **443** (HTTPS)

Verify installation:

```bash
docker --version        # >= 24.0
docker compose version  # >= v2.20
```

## Quick Production Deploy

### 1. Clone and configure

```bash
git clone https://github.com/themayursinha/verity-trust-copilot.git
cd verity-trust-copilot
cp .env.example .env
```

### 2. Edit `.env`

Open `.env` and set **all** required values:

| Variable | How to Generate | Example |
|---|---|---|
| `POSTGRES_PASSWORD` | `openssl rand -base64 32` | Strong random password |
| `SECRET_KEY` | `openssl rand -hex 64` | 128-character hex string |
| `CORS_ORIGINS` | Your domain with protocol | `https://app.yourcompany.com` |
| `SENTRY_DSN` | From sentry.io (optional) | `https://...@sentry.io/123` |

### 3. Generate JWT RSA keys

```bash
bash scripts/generate-keys.sh
```

This creates `secrets/jwt_private.pem` and `secrets/jwt_public.pem` with restricted permissions (600).

### 4. Start services

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

This starts four containers: `postgres`, `redis`, `backend` (FastAPI), and `frontend` (Nginx serving the React SPA).

### 5. Verify

```bash
# Check container health
docker compose ps

# Verify backend health endpoint
curl -s http://localhost:8000/api/v1/health

# Open the app
curl -s -o /dev/null -w "%{http_code}" http://localhost:80/
# Should return 200
```

Open `http://<your-server-ip>` in a browser to access the landing page.

## HTTPS Setup

The frontend container runs Nginx on port 80. For production, always put it behind a reverse proxy with TLS termination. Choose one of the following:

### Option A: Caddy (easiest)

Caddy obtains and renews Let's Encrypt certificates automatically.

```bash
# Install Caddy
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install caddy
```

Create `/etc/caddy/Caddyfile`:

```caddyfile
app.yourcompany.com {
    reverse_proxy localhost:80
    encode gzip
}
```

Reload Caddy:

```bash
sudo systemctl reload caddy
```

### Option B: Traefik as a Docker service

Add Traefik to your `docker-compose.prod.yml`:

```yaml
services:
  traefik:
    image: traefik:v3.1
    restart: unless-stopped
    command:
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@yourcompany.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "./letsencrypt:/letsencrypt"

  frontend:
    # Remove the ports directive from frontend and add labels:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.frontend.rule=Host(`app.yourcompany.com`)"
      - "traefik.http.routers.frontend.entrypoints=websecure"
      - "traefik.http.routers.frontend.tls.certresolver=letsencrypt"
```

### Option C: Nginx + Certbot

Install Nginx and Certbot, then create `/etc/nginx/sites-available/verity`:

```nginx
server {
    listen 80;
    server_name app.yourcompany.com;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and get a certificate:

```bash
sudo ln -s /etc/nginx/sites-available/verity /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d app.yourcompany.com
```

### Note on backend exposure

The backend runs on port 8000. In production, **do not expose port 8000 to the internet**. Comment out or remove the `ports` mapping on the backend service in your override file if your reverse proxy is on the same host. If using Docker networking, the frontend (Nginx) can proxy API calls to `http://backend:8000` internally.

## Database Backups

### Automated daily backups

Add to crontab (`crontab -e`):

```cron
0 2 * * * cd /opt/verity-trust-copilot && bash scripts/backup.sh
```

### Manual backup

```bash
bash scripts/backup.sh
```

Backups are gzipped SQL dumps written to `./backups/verity_<timestamp>.sql.gz`.

### Off-site backup

Sync backups to an external location:

```bash
# rsync to remote server
rsync -avz ./backups/ user@backup-server:/backups/verity/

# Or upload to S3-compatible storage
aws s3 sync ./backups/ s3://my-verity-backups/ --storage-class STANDARD_IA
```

### Restore

```bash
bash scripts/restore.sh backups/verity_20260524_020000.sql.gz
```

**Important:** The restore script overwrites the current database. Stop the backend container first to avoid conflicts:

```bash
docker compose stop backend
bash scripts/restore.sh backups/verity_20260524_020000.sql.gz
docker compose start backend
```

## Upgrading

### Standard upgrade

```bash
cd /opt/verity-trust-copilot

# Pull latest changes
git pull origin main

# Rebuild and restart backend + frontend
docker compose -f docker-compose.yml -f docker-compose.prod.yml build backend frontend
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d backend frontend

# Run any new database migrations
docker compose exec backend alembic upgrade head
```

### Zero-downtime upgrade (with multiple backend replicas)

```bash
# Scale backend to 2 instances
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale backend=2

# Rebuild the image
docker compose -f docker-compose.yml -f docker-compose.prod.yml build backend

# Restart one at a time (Docker Compose handles rolling restarts poorly; use a
# process manager like Docker Swarm or use separate commands)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale backend=2 --no-recreate backend

# Run migrations on one instance
docker compose exec backend alembic upgrade head

# Scale back down
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale backend=1
```

### Rollback

If a migration fails, revert it:

```bash
docker compose exec backend alembic downgrade -1
```

Then revert the code and rebuild:

```bash
git checkout <previous-tag>
docker compose -f docker-compose.yml -f docker-compose.prod.yml build backend frontend
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Health Monitoring

### API health check

```bash
curl http://localhost:8000/api/v1/health
# Expected: {"status":"healthy","version":"0.1.0"}
```

### Prometheus metrics

Metrics are exposed at `/metrics` on the backend. Scrape endpoint for Prometheus:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: "verity"
    scrape_interval: 30s
    static_configs:
      - targets: ["backend:8000"]
```

Available metrics include request counts, latency histograms, error rates, and database connection pool stats.

### Container health

```bash
docker compose ps
```

Expected state: all services `healthy` (or `Up` if using Compose v1).

### Log streaming

```bash
# All services
docker compose logs -f

# Backend only
docker compose logs -f backend

# Last 100 lines with timestamps
docker compose logs --tail 100 -t backend
```

### Resource usage

```bash
docker stats --no-stream
```

### Disk space

```bash
# Docker volumes and images
docker system df

# Backup directory size
du -sh ./backups/
```

### Systemd service (recommended)

Create `/etc/systemd/system/verity.service`:

```ini
[Unit]
Description=Verity Trust Copilot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/verity-trust-copilot
ExecStart=/usr/bin/docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.yml -f docker-compose.prod.yml down
ExecReload=/usr/bin/docker compose -f docker-compose.yml -f docker-compose.prod.yml restart

[Install]
WantedBy=multi-user.target
```

Enable auto-start on boot:

```bash
sudo systemctl daemon-reload
sudo systemctl enable verity
```

## Troubleshooting

### Database connection errors

```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Check PostgreSQL health:**

```bash
docker compose ps postgres
# State should be "healthy"

docker compose logs postgres --tail 50
```

**Verify credentials** match between `.env` and the Docker Compose environment block. The `POSTGRES_PASSWORD` in `.env` must match `POSTGRES_PASSWORD` used in `docker-compose.prod.yml`.

**Check if port is in use:**

```bash
sudo ss -tlnp | grep 5432
```

### Migration failures

```
alembic.exc.ProgrammingError: relation "x" already exists
```

This happens if the database was partially migrated. Identify the stuck revision:

```bash
docker compose exec backend alembic current
docker compose exec backend alembic history
```

Manually mark a revision as complete:

```bash
docker compose exec backend alembic stamp <revision_id>
```

Then retry:

```bash
docker compose exec backend alembic upgrade head
```

### Frontend fails to load or shows blank page

```bash
# Check nginx is running
docker compose logs frontend --tail 20

# Verify the built assets exist
docker compose exec frontend ls /usr/share/nginx/html/

# Check nginx config
docker compose exec frontend nginx -t
```

If the frontend loads but API calls fail, verify `VITE_API_URL` is set correctly in the frontend build (or ensure Nginx proxies `/api` requests to the backend).

### JWT token validation errors

Symptoms: login succeeds but all API calls return 401.

```bash
# Verify keys exist and have correct permissions
ls -la secrets/
# jwt_private.pem should have -rw-------
# jwt_public.pem should have -rw-r--r--

# Regenerate if needed
bash scripts/generate-keys.sh
docker compose restart backend
```

### Redis connection errors

```bash
docker compose ps redis
docker compose logs redis --tail 30
```

Redis is used for refresh token storage and rate limiting. If Redis is down, login and token refresh will fail.

### Container exits immediately

```bash
docker compose logs backend --tail 50
```

Common causes:
- Missing `.env` variables (check `SECRET_KEY`, `POSTGRES_PASSWORD`)
- Ports already in use
- Missing JWT key files in `secrets/`
- Insufficient disk space (`df -h`)

### Session/Cookie not persisting

Verify `CORS_ORIGINS` in `.env` exactly matches the browser origin (protocol + hostname). No trailing slashes. Multiple origins can be comma-separated.

## Scaling Considerations

### Adding backend workers

If your user base grows and the single backend instance becomes CPU-bound (BM25 retrieval is CPU-intensive), scale horizontally:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale backend=3
```

**Important considerations:**
- Place a load balancer (Nginx, HAProxy, Traefik) in front of the backend instances.
- JWT RS256 tokens are stateless — any instance can validate them without coordination.
- WebSocket connections (if enabled) require sticky sessions on the load balancer.

### PostgreSQL tuning

Edit `docker-compose.prod.yml` to tune Postgres for your hardware:

```yaml
postgres:
  command:
    - "postgres"
    - "-c"
    - "shared_buffers=256MB"
    - "-c"
    - "effective_cache_size=768MB"
    - "-c"
    - "work_mem=16MB"
    - "-c"
    - "maintenance_work_mem=64MB"
```

**Rule of thumb** for a 2 GB server:
- `shared_buffers`: 25% of RAM (~512 MB)
- `effective_cache_size`: 50-75% of RAM
- `work_mem`: 2-4 MB per expected concurrent connection

### Redis persistence

By default, Redis in the production compose file uses an append-only file (AOF) stored in the `redisdata` volume. For higher durability, consider enabling RDB snapshots:

```yaml
redis:
  command: redis-server --appendonly yes --save 900 1 --save 300 10 --save 60 10000
```

### Disk space management

**Docker cleanup:**

```bash
# Remove unused images, containers, and volumes
docker system prune -a --volumes

# Target only build cache
docker builder prune --keep-storage 5GB
```

**Log rotation** for Docker containers:

In `/etc/docker/daemon.json`:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Restart Docker: `sudo systemctl restart docker`

**Backup retention script** (add to crontab weekly):

```bash
#!/usr/bin/env bash
# Delete backups older than 30 days
find /opt/verity-trust-copilot/backups -name "verity_*.sql.gz" -mtime +30 -delete
```

## Security Hardening Checklist

- [ ] Change `POSTGRES_PASSWORD` from default
- [ ] Generate `SECRET_KEY` with `openssl rand -hex 64`
- [ ] Generate RSA JWT keys (not using the default symmetric fallback)
- [ ] Set `CORS_ORIGINS` to your exact domain
- [ ] Enable HTTPS via Caddy, Traefik, or Nginx + Certbot
- [ ] Restrict backend port 8000 from public access (firewall/security group)
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure `SENTRY_DSN` for error monitoring
- [ ] Set up database backups (cron + off-site sync)
- [ ] Apply OS-level firewall rules (`ufw` / `iptables`)
- [ ] Run `chmod 600 .env` to restrict environment file access
- [ ] Keep Docker and host OS updated (`unattended-upgrades` on Ubuntu)
- [ ] Review Dockerfile for pinned image digests in high-security environments
