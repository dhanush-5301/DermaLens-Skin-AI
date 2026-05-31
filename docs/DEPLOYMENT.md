# Deployment Guide

This guide covers deploying DermaLens AI to production environments.

---

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Production on Linux Server](#production-on-linux-server)
4. [Cloud Platforms](#cloud-platforms)
5. [Monitoring & Logging](#monitoring--logging)
6. [Security Hardening](#security-hardening)

---

## Local Development

### Prerequisites

- Python 3.11+
- Virtual environment (venv/conda)
- ~2 GB free disk space

### Installation

```bash
# 1. Clone repository
git clone https://github.com/YOUR_USERNAME/dermalens-ai.git
cd dermalens-ai

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY

# 5. Run development server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Server runs at:** `http://localhost:8000`

### Hot Reload

The `--reload` flag automatically restarts when code changes. Ideal for development.

---

## Docker Deployment

### Prerequisites

- Docker Engine (20.10+)
- Docker Compose (1.29+)
- ~3 GB disk space

### Quick Start

```bash
# 1. Clone repository
git clone https://github.com/YOUR_USERNAME/dermalens-ai.git
cd dermalens-ai

# 2. Configure environment
cp .env.example .env
# Edit .env with your settings

# 3. Build & run
docker-compose up --build

# 4. Access application
# Open browser: http://localhost:8000
```

### Production Docker Compose

For production, use optimized settings:

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  dermalens:
    image: dermalens-ai:latest
    container_name: dermalens-prod
    restart: always
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - LOG_LEVEL=info
      - PORT=8000
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

**Run:** `docker-compose -f docker-compose.prod.yml up -d`

### Building Custom Image

```bash
# Build image
docker build -t dermalens-ai:v1.0 .

# Run container
docker run -d \
  --name dermalens \
  -p 8000:8000 \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/logs:/app/logs \
  dermalens-ai:v1.0

# View logs
docker logs -f dermalens

# Stop container
docker stop dermalens
```

---

## Production on Linux Server

### Requirements

- Ubuntu 20.04 LTS or later
- 2+ CPU cores
- 4+ GB RAM
- 10+ GB storage
- NVIDIA GPU (optional, for faster inference)

### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip nginx supervisor

# Create app user
sudo useradd -m -s /bin/bash dermalens
sudo su - dermalens
```

### Step 2: Application Deployment

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/dermalens-ai.git
cd dermalens-ai

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Configure environment
cp .env.example .env
nano .env  # Add ANTHROPIC_API_KEY
```

### Step 3: Systemd Service

Create `/etc/systemd/system/dermalens.service`:

```ini
[Unit]
Description=DermaLens AI Application
After=network.target

[Service]
User=dermalens
WorkingDirectory=/home/dermalens/dermalens-ai
ExecStart=/home/dermalens/dermalens-ai/venv/bin/gunicorn \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    backend.main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable & start:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable dermalens
sudo systemctl start dermalens
sudo systemctl status dermalens
```

### Step 4: Nginx Reverse Proxy

Create `/etc/nginx/sites-available/dermalens`:

```nginx
upstream dermalens {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL certificate (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy to backend
    location / {
        proxy_pass http://dermalens;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        client_max_body_size 15M;
    }

    # Static files caching
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

**Enable site:**

```bash
sudo ln -s /etc/nginx/sites-available/dermalens /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 5: SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

---

## Cloud Platforms

### AWS Deployment (EC2 + ALB)

```bash
# 1. Launch EC2 instance (Ubuntu 20.04, t3.medium)
# 2. SSH into instance
ssh -i key.pem ubuntu@your-instance-ip

# 3. Follow "Production on Linux Server" steps above

# 4. Create ALB Target Group
# - Register EC2 instance
# - Port 443 (HTTPS)
# - Health check: /health

# 5. Create Application Load Balancer
# - Target group: dermalens
# - Listeners: 80 (HTTP) → 443 (HTTPS)
# - SSL certificate: ACM

# 6. Auto Scaling Group (optional)
# - Min: 1 instance
# - Max: 3 instances
# - Scale on CPU > 70%
```

### Google Cloud (Cloud Run)

```bash
# 1. Create Dockerfile (included in repo)

# 2. Build & push image
gcloud builds submit --tag gcr.io/YOUR_PROJECT/dermalens

# 3. Deploy to Cloud Run
gcloud run deploy dermalens \
  --image gcr.io/YOUR_PROJECT/dermalens \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --allow-unauthenticated \
  --set-env-vars ANTHROPIC_API_KEY=sk-ant-...
```

### Heroku Deployment

```bash
# 1. Install Heroku CLI
curl https://cli.heroku.com/install.sh | sh

# 2. Login
heroku login

# 3. Create app
heroku create dermalens-ai

# 4. Add buildpack
heroku buildpacks:add heroku/python

# 5. Set environment variables
heroku config:set ANTHROPIC_API_KEY=sk-ant-...

# 6. Deploy
git push heroku main
```

---

## Monitoring & Logging

### Application Health Check

```bash
# Manual health check
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "ok",
#   "model_loaded": true,
#   "version": "1.0.0"
# }
```

### Log Monitoring

```bash
# View application logs
tail -f logs/dermalens.log

# Filter error logs
grep "ERROR" logs/dermalens.log

# Monitor in real-time
journalctl -u dermalens -f
```

### Performance Monitoring

```bash
# CPU/Memory usage
top -p $(pgrep -f gunicorn)

# Disk usage
df -h

# Network connections
netstat -tuln | grep 8000
```

### Cloud Monitoring (AWS CloudWatch)

```bash
# Push custom metrics
aws cloudwatch put-metric-data \
  --namespace DermaLens \
  --metric-name InferenceTime \
  --value 250 \
  --unit Milliseconds
```

---

## Security Hardening

### 1. Environment Variables

```bash
# Never hardcode secrets!
# Always use .env files

# Production example:
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
LOG_LEVEL=info
PORT=8000
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### 2. Firewall Rules

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw default deny incoming
sudo ufw enable
```

### 3. File Permissions

```bash
# Restrict access to sensitive files
chmod 600 .env
chmod 755 backend/
chmod 644 models/*
sudo chown -R dermalens:dermalens /home/dermalens/dermalens-ai
```

### 4. API Rate Limiting

Add to `backend/main.py`:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/analyze")
@limiter.limit("10/minute")  # 10 requests per minute per IP
async def analyze(request: Request, file: UploadFile):
    ...
```

### 5. CORS Security

```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://www.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 6. Request Size Limits

```python
# Prevent large uploads
app.add_middleware(
    BaseHTTPMiddleware,
    dispatch=limit_upload_size(max_size=15 * 1024 * 1024)
)
```

### 7. HTTPS Only

```nginx
# In Nginx configuration
add_header Strict-Transport-Security "max-age=31536000" always;
```

---

## Backup & Recovery

### Database Backup (if using PostgreSQL)

```bash
# Daily backup
0 2 * * * pg_dump dermalens > /backups/dermalens-$(date +\%Y\%m\%d).sql

# Store on S3
aws s3 cp /backups/dermalens-*.sql s3://your-backup-bucket/
```

### Application Backup

```bash
# Backup models and configs
tar -czf dermalens-backup-$(date +%Y%m%d).tar.gz \
  models/ \
  .env \
  logs/
```

---

## Troubleshooting

### Application won't start

```bash
# Check logs
journalctl -u dermalens -n 50

# Verify virtual environment
which python

# Check port availability
lsof -i :8000
```

### High memory usage

```bash
# Reduce worker count
workers = 2  # instead of 4

# Restart service
sudo systemctl restart dermalens
```

### SSL certificate errors

```bash
# Renew certificate
sudo certbot renew --force-renewal

# Check expiration
sudo certbot certificates
```

### API timeouts

```bash
# Increase timeout in Nginx
proxy_read_timeout 30s;
proxy_connect_timeout 30s;
```

---

<div align="center">

**Need help?** Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more solutions.

</div>
