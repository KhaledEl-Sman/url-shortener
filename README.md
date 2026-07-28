# ⚡ Snip — URL Shortener

Phase 0 of the **flask-observability-platform** resume project.  
A production-ready URL shortener with auth, click analytics, Redis caching, structured logging, and Faro RUM.

## Stack

| Layer       | Technology                        |
|-------------|-----------------------------------|
| Frontend    | Vanilla JS + Nginx (ESLint)       |
| Backend     | Flask 3 + Gunicorn + SQLAlchemy   |
| Database    | PostgreSQL 16                     |
| Cache       | Redis 7                           |
| Log shipper | Grafana Alloy (sidecar)           |
| RUM         | Grafana Faro Web SDK              |
| Tracing     | OpenTelemetry → Alloy → Tempo     |

## Quick start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env — set SECRET_KEY, JWT_SECRET_KEY, POSTGRES_PASSWORD

# 2. Build and start
make build
make up

# 3. Run DB migrations
make db-migrate

# 4. Open the app
open http://localhost
```

## Endpoints

| Method | Path                          | Auth | Description            |
|--------|-------------------------------|------|------------------------|
| GET    | /health                       | —    | Service health check   |
| GET    | /metrics                      | —    | Prometheus metrics     |
| POST   | /api/auth/register            | —    | Register user          |
| POST   | /api/auth/login               | —    | Login → JWT token      |
| POST   | /api/auth/logout              | JWT  | Revoke token           |
| GET    | /api/auth/me                  | JWT  | Current user           |
| POST   | /api/links                    | JWT  | Create short link      |
| GET    | /api/links                    | JWT  | List user's links      |
| DELETE | /api/links/\<code\>           | JWT  | Delete link            |
| GET    | /api/analytics/\<code\>       | JWT  | Click analytics        |
| GET    | /\<short_code\>               | —    | Redirect (302)         |

## Dev commands

```bash
make lint        # Run ESLint + flake8/black/isort
make test        # Run pytest suite
make logs        # Tail all container logs
make db-shell    # psql prompt
make redis-cli   # Redis CLI
make health      # Check /health endpoints
```

## Observability

- **Structured logs** → Alloy → (ready for Loki in Phase 8)
- **Prometheus metrics** → `/metrics` (counters, histograms per route)
- **Faro RUM** → frontend ships to Alloy at `:12347/collect`
- **OTel traces** → backend → Alloy → (ready for Tempo in Phase 8)
- **Alloy UI** → http://localhost:12348

## Project structure

```
url-shortener/
├── frontend/          Vanilla JS + Nginx
│   ├── css/           Stylesheet
│   ├── js/            api.js · auth.js · monitoring.js
│   └── pages/         login.html · register.html · dashboard.html
├── backend/           Flask application
│   ├── src/
│   │   ├── main.py            App factory
│   │   ├── extensions.py      Shared extensions
│   │   ├── models.py          User, Link, Click
│   │   └── routes/            auth · links · redirect · analytics
│   └── tests/
├── alloy/             config.alloy — log pipeline
├── postgres/          init.sql
├── docker-compose.yml Full local stack
└── Makefile           Dev shortcuts
```

## Next phases

This repo is Phase 0. Subsequent phases add:

- **Phase 1** — GitHub Actions CI (lint, test, Trivy, SonarQube, Docker Hub push)
- **Phase 2** — Terraform (GKE cluster)
- **Phase 3** — Helm chart + Ansible
- **Phase 4** — ArgoCD GitOps
- **Phase 5** — Full observability (Prometheus, Grafana, Loki, Tempo, Pyroscope, k6…)
