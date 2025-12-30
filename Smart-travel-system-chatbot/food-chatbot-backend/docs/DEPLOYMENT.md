# Deployment Guide

This guide covers deploying the Food Chatbot Backend to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Options](#deployment-options)
3. [Docker Deployment](#docker-deployment)
4. [SSL/TLS Setup](#ssltls-setup)
5. [Environment Configuration](#environment-configuration)
6. [Monitoring Setup](#monitoring-setup)
7. [Scaling](#scaling)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Docker & Docker Compose v2.0+
- Domain name (for SSL)
- Groq API key(s)
- 2GB+ RAM, 2+ CPU cores

## Deployment Options

| Option | Best For | Complexity |
|--------|----------|------------|
| Docker Compose | Single server, small teams | Low |
| Kubernetes | Large scale, auto-scaling | High |
| Cloud Run (GCP) | Serverless, pay-per-use | Medium |
| Railway/Render | Quick deployment | Low |

---

## Docker Deployment

### 1. Clone and Configure

```bash
# Clone repository
git clone https://github.com/your-repo/food-chatbot-backend.git
cd food-chatbot-backend

# Copy production environment file
cp .env.example .env.production

# Edit configuration
nano .env.production
```

### 2. Production Environment

Edit `.env.production`:

```env
# API Keys (Required)
GROQ_API_KEY=gsk_your_main_key
GROQ_BACKUP_KEYS=gsk_backup1,gsk_backup2

# Security (Generate strong secrets!)
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000

# CORS (Add your frontend domains)
CORS_ORIGINS=https://your-frontend.com,https://www.your-frontend.com

# Monitoring (Optional but recommended)
SENTRY_DSN=https://your-sentry-dsn
ENABLE_METRICS=true

# Database (PostgreSQL for production)
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/food_chatbot

# Redis (Optional caching)
REDIS_URL=redis://redis:6379/0
```

### 3. Build and Deploy

```bash
# Build images
docker-compose -f docker-compose.yml build

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api
```

### 4. Docker Compose Production Setup

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    restart: always
    environment:
      - ENVIRONMENT=production
    env_file:
      - .env.production
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  postgres:
    image: postgres:16-alpine
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.prod.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
      - ./nginx/certbot:/var/www/certbot
    depends_on:
      - api

volumes:
  postgres_data:
  redis_data:
```

---

## SSL/TLS Setup

### Option 1: Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d api.yourdomain.com

# Auto-renewal (add to crontab)
0 0 1 * * certbot renew --quiet
```

### Option 2: Cloudflare (Free)

1. Add domain to Cloudflare
2. Set SSL mode to "Full (strict)"
3. Cloudflare handles certificates automatically

### Option 3: Self-signed (Development only)

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout ssl/privkey.pem \
  -out ssl/fullchain.pem \
  -subj "/CN=localhost"
```

### Nginx SSL Configuration

```nginx
# nginx/nginx.prod.conf
server {
    listen 80;
    server_name api.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    location / {
        proxy_pass http://api:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://api:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Environment Configuration

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GROQ_API_KEY` | Primary Groq API key | `gsk_...` |
| `JWT_SECRET_KEY` | JWT signing key (32+ chars) | Random string |
| `ENVIRONMENT` | Environment name | `production` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | localhost | Allowed origins |
| `SENTRY_DSN` | None | Sentry error tracking |
| `REDIS_URL` | None | Redis cache URL |
| `DATABASE_URL` | SQLite | PostgreSQL URL |

### Generate Secrets

```bash
# JWT Secret
openssl rand -hex 32

# Output:
# a1b2c3d4e5f6...
```

---

## Monitoring Setup

### 1. Prometheus Metrics

Access at `http://your-server:8000/metrics`

Key metrics:
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency
- `chat_messages_total` - Chat message count
- `ai_response_time_seconds` - AI response time

### 2. Sentry Error Tracking

```bash
# Add to .env.production
SENTRY_DSN=https://abc123@o123456.ingest.sentry.io/1234567
```

### 3. Grafana Dashboard

```bash
# Start with monitoring profile
docker-compose --profile monitoring up -d

# Access Grafana
open http://your-server:3001

# Default credentials: admin/admin
```

### 4. Health Checks

```bash
# Basic health
curl https://api.yourdomain.com/health

# Detailed readiness
curl https://api.yourdomain.com/ready
```

---

## Scaling

### Horizontal Scaling with Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.prod.yml food-chatbot

# Scale API service
docker service scale food-chatbot_api=3
```

### Kubernetes Deployment

```yaml
# k8s/deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: food-chatbot-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: food-chatbot-api
  template:
    metadata:
      labels:
        app: food-chatbot-api
    spec:
      containers:
      - name: api
        image: food-chatbot-backend:latest
        ports:
        - containerPort: 8000
        resources:
          limits:
            cpu: "2"
            memory: "2Gi"
          requests:
            cpu: "500m"
            memory: "512Mi"
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        envFrom:
        - secretRef:
            name: food-chatbot-secrets
```

### Load Balancing

With multiple instances, use Nginx upstream:

```nginx
upstream api_servers {
    least_conn;
    server api1:8000;
    server api2:8000;
    server api3:8000;
}

server {
    location / {
        proxy_pass http://api_servers;
    }
}
```

---

## Troubleshooting

### Common Issues

#### 1. Container won't start

```bash
# Check logs
docker-compose logs api

# Common causes:
# - Missing .env file
# - Invalid API key
# - Port already in use
```

#### 2. Database connection failed

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U food_chatbot -d food_chatbot

# Check logs
docker-compose logs postgres
```

#### 3. CORS errors

```bash
# Verify CORS_ORIGINS in .env.production
# Must match exactly (including https://)
CORS_ORIGINS=https://your-frontend.com
```

#### 4. SSL certificate issues

```bash
# Check certificate
openssl s_client -connect api.yourdomain.com:443

# Verify certificate files
ls -la ssl/

# Check Nginx logs
docker-compose logs nginx
```

#### 5. Memory issues

```bash
# Check memory usage
docker stats

# Increase limits in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G
```

### Debug Mode

```bash
# Enable debug logging temporarily
docker-compose exec api sh -c 'LOG_LEVEL=DEBUG uvicorn main:app --reload'
```

### Performance Testing

```bash
# Run load tests
locust -f tests/load/locustfile.py --host=https://api.yourdomain.com
```

---

## Quick Reference

```bash
# Start production
docker-compose -f docker-compose.prod.yml up -d

# Stop
docker-compose down

# Restart API only
docker-compose restart api

# View logs (follow)
docker-compose logs -f api

# Backup database
docker-compose exec postgres pg_dump -U food_chatbot food_chatbot > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T postgres psql -U food_chatbot food_chatbot

# Update to latest
git pull
docker-compose build
docker-compose up -d
```

---

*Last updated: December 2025*
