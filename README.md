# AIOps Assistant — Phase 1: Project Foundation

A secure, production-ready full-stack foundation for an AI-powered AIOps platform:
React frontend, FastAPI backend, PostgreSQL, JWT auth, RBAC, Docker Compose,
structured logging, and Swagger/OpenAPI docs. This is the base that Phases 2–11
(observability, log intelligence, an AI agent, incident detection, root-cause
analysis, alerting, and production deployment) build on.

## Tech stack

| Layer      | Choice                                            |
|------------|----------------------------------------------------|
| Frontend   | React + TypeScript, Vite, Tailwind CSS, React Query |
| Backend    | FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2      |
| Database   | PostgreSQL 16                                      |
| Auth       | JWT (access + refresh tokens), RBAC                |
| Logging    | structlog + loguru, JSON in production             |
| Container  | Docker, Docker Compose                             |

## Project structure

```
aiops-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, middleware, router wiring
│   │   ├── core/               # config, logging
│   │   ├── api/                # routes + shared dependencies
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── services/            # business logic
│   │   ├── repositories/        # data-access layer
│   │   ├── db/                  # engine/session, init/seed
│   │   ├── middleware/          # request logging
│   │   └── auth/                # JWT + RBAC
│   ├── alembic/                 # migrations
│   ├── tests/                   # pytest suite
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/                # Login, Register, Dashboard, Incidents,
│   │   │                          Monitoring, AI Chat, Settings
│   │   ├── layouts/              # AppShell (sidebar + header)
│   │   ├── contexts/             # AuthContext
│   │   ├── services/             # API client + auth service
│   │   └── components/
│   └── Dockerfile
├── docker/, kubernetes/, openshift/, monitoring/   # reserved for later phases
├── docs/, scripts/, .github/workflows/
├── docker-compose.yml
└── .env.example
```

## Quick start (Docker Compose — recommended)

```bash
cp .env.example .env      # edit JWT_SECRET_KEY before any real deployment
docker compose up --build
```

This starts three containers:

- **postgres** — PostgreSQL 16 on `5432`
- **backend** — FastAPI on `8000` (runs Alembic migrations automatically on boot)
- **frontend** — React app served by nginx on `5173`

Then open:

- Frontend: http://localhost:5173
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/api/v1/health

Create your first admin user:

```bash
./scripts/create_admin.sh admin@example.com "Admin User" "StrongPassword123"
```

Then sign in at http://localhost:5173/login.

## Running without Docker

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Point DATABASE_URL at a Postgres instance you have running locally,
# or use docker compose up postgres to start just the database.
cp ../.env.example .env

alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## Authentication flow

- `POST /api/v1/auth/register` — create a user with a role (`admin`, `devops_engineer`, `viewer`)
- `POST /api/v1/auth/login` — returns an access token (30 min) and refresh token (7 days)
- `POST /api/v1/auth/refresh` — exchange a refresh token for a new pair
- `POST /api/v1/auth/logout` — stateless client-side discard
- `GET /api/v1/auth/me` — current user (requires `Authorization: Bearer <token>`)

The frontend's axios client automatically refreshes an expired access token
and retries the failed request once, before redirecting to `/login`.

## RBAC permission matrix

| Role              | Permissions                              |
|-------------------|-------------------------------------------|
| `admin`           | Full access                                |
| `devops_engineer` | Monitoring, AI Chat, Incidents             |
| `viewer`          | Read-only                                  |

Enforced server-side via `app/auth/rbac.py` (`require_admin`,
`require_devops_or_admin`, `require_any_role`) — see `app/api/routes/users.py`
for example usage.

## Testing

```bash
cd backend
pytest -v
```

Tests run against an in-memory SQLite database, so no running Postgres is
required. Coverage includes: health checks, registration, login (success and
failure), token-protected routes, and RBAC enforcement.

## Logging

Every request is logged as structured JSON (method, path, status, duration,
request ID) via `app/middleware/logging_middleware.py`. Authentication events
(`login_success`, `login_failed`, `user_registered`, `token_refreshed`) are
logged from `app/services/auth_service.py`. Set `LOG_JSON=false` in `.env`
for human-readable console output during local development.

## Environment variables

See `.env.example` for the full list. Nothing sensitive is hardcoded — all
config loads through `app/core/config.py` (pydantic-settings), including
placeholders for integrations wired up in later phases (OpenAI, SMTP,
Prometheus, Grafana, Loki, Jenkins).

## Phase 1 validation checklist

- [x] GitHub-ready repository structure (`backend/`, `frontend/`, `docker/`, `kubernetes/`, `openshift/`, `monitoring/`, `docs/`, `scripts/`, `.github/`)
- [x] FastAPI backend running with Swagger docs at `/docs`
- [x] React frontend running with routing (`react-router-dom`) across 7 pages
- [x] PostgreSQL connected via SQLAlchemy; Alembic migration creates all tables
- [x] `docker compose up --build` starts frontend, backend, and database together
- [x] JWT authentication: register, login, refresh, logout, `/me`
- [x] RBAC restricts access by role (admin / devops_engineer / viewer)
- [x] Structured JSON logging (structlog) on every request and auth event
- [x] Environment variables managed via `.env` / pydantic-settings, nothing hardcoded
- [x] Pytest suite covering health, auth, and RBAC — all passing

## Phase 2 — Monitoring Platform

Phase 2 turns the foundation into a real-time monitoring platform.

**Monitoring stack** (`docker compose up --build` now also starts):

| Service            | Port | Purpose                                   |
|---------------------|------|--------------------------------------------|
| Prometheus          | 9090 | Metric collection, alert rule evaluation   |
| Node Exporter       | 9100 | Host-level CPU/memory/disk/network metrics |
| kube-state-metrics  | 8080 | Kubernetes object state (no-op outside k8s)|
| Alertmanager        | 9093 | Alert routing → webhooks the backend       |
| Grafana             | 3000 | Dashboards (admin/admin by default)        |

**New backend endpoints** (all under `/api/v1`, all RBAC-protected):

```
GET  /metrics/{cpu|memory|disk|network|load|filesystem}
GET  /metrics/history/{cpu|memory|network}?hours=24
GET  /metrics/prometheus            # self-metrics exposition for Prometheus to scrape

GET  /kubernetes/pods[?namespace=]
GET  /kubernetes/pods/{pod_name}
GET  /kubernetes/nodes
GET  /kubernetes/deployments[?namespace=]
GET  /kubernetes/namespaces
GET  /kubernetes/services[?namespace=]
GET  /kubernetes/replicasets[?namespace=]
GET  /kubernetes/statefulsets[?namespace=]

GET  /cluster/health

GET  /jenkins/jobs
GET  /jenkins/builds?job_name=<name>
GET  /jenkins/failed

GET  /alerts
GET  /alerts/active
GET  /alerts/history
POST /alerts/webhook                # Alertmanager pushes here
```

**Graceful degradation.** None of Prometheus, Kubernetes, or Jenkins are
required for the stack to boot. Each service client checks connectivity up
front:

- No Prometheus reachable → `/metrics/*` returns `"available": false` instead of erroring.
- No kubeconfig / not in-cluster → `/kubernetes/*` returns `"connected": false, "items": []`.
- No `JENKINS_URL` set → `/jenkins/*` returns `"configured": false, "items": []`.

This means the frontend renders correctly (with "not connected" hints)
whether or not you've stood up the full monitoring stack yet.

**Alerting.** Two paths converge on the same alert pipeline (save → email →
log):

1. Alertmanager evaluates `monitoring/prometheus/alert_rules.yml`
   (CPU/memory > 90%, disk > 85%, target down) and pushes to
   `POST /alerts/webhook`.
2. A lightweight in-process scheduler (`app/core/scheduler.py`) polls the
   same thresholds every 60 seconds as a backstop, so alerts still fire in
   local dev without a running Alertmanager.

Configure `SMTP_HOST` / `SMTP_USER` / `SMTP_PASSWORD` in `.env` to enable
real email delivery (Gmail, Microsoft 365, or any SMTP relay); without it,
alerts are still saved and logged, just not emailed.

**New frontend pages:** Infrastructure (system-level gauges + cluster
rollup), Kubernetes (pods/nodes/deployments tables), Metrics (live gauges +
24h history charts), Alerts (active + history), Jenkins (job/build status).
The Dashboard page now shows live gauges, active alert count, and cluster
node count instead of Phase 1's static placeholders.

**Database additions:** `metric_history`, `pod_metrics`, `cluster_metrics`,
`jenkins_metrics` (Alembic migration `0002`).

### Phase 2 validation checklist

- [x] Prometheus, Node Exporter, Alertmanager, Grafana, kube-state-metrics added to Docker Compose
- [x] `prometheus_service.py` executes PromQL and parses responses, with time-range support
- [x] `/metrics/*` and `/metrics/history/*` endpoints live for all six metrics (cpu, memory, disk, network, load, filesystem)
- [x] `kubernetes_service.py` + `/kubernetes/*` endpoints (pods, nodes, deployments, namespaces, services, replicasets, statefulsets)
- [x] `/kubernetes/pods/{name}` returns per-pod CPU/memory/status/restarts
- [x] `/cluster/health` aggregates Kubernetes + Prometheus into one response
- [x] `jenkins_service.py` + `/jenkins/jobs`, `/jenkins/builds`, `/jenkins/failed`
- [x] Alert Management: `/alerts`, `/alerts/active`, `/alerts/history`, `/alerts/webhook`, persisted to `alerts` / `notification_logs`
- [x] Email notifications via SMTP, with graceful no-op when unconfigured
- [x] Frontend: Infrastructure, Kubernetes, Metrics, Alerts, Jenkins pages with live-polling widgets
- [x] `metric_history`, `pod_metrics`, `cluster_metrics`, `jenkins_metrics` tables (migration `0002`)
- [x] Pytest coverage for graceful degradation + alert webhook create/resolve flow + all 6 history metrics

> **Post-deploy fix:** history originally only allow-listed cpu/memory/network
> even though the underlying Prometheus query map already covered all six
> metrics. Fixed by widening `VALID_HISTORY_METRICS` to match `VALID_METRICS`.
> While in there, `memory`, `disk`, `load`, and `filesystem` queries were
> also wrapped in `avg(...)` so they resolve to a single series regardless
> of how many nodes/mountpoints/interfaces Prometheus is scraping — needed
> for correct behavior on anything beyond a single-node dev box (Kind,
> OpenShift, multi-node clusters).

## What's next

Phase 3 (Log Intelligence) adds Loki/OpenSearch log aggregation and a
centralized log explorer. Phase 4 introduces the AI agent that reasons over
everything Phase 2 now collects.

## Module 2.6 — Alert Management (complete)

Alerts now have a full lifecycle instead of just active/resolved:

```
active -> acknowledged -> resolved
```

New endpoints:

```
GET   /api/v1/alerts?severity=critical&source=prometheus&resolved=false&start=...&end=...
GET   /api/v1/alerts/dashboard      # { active_alerts, critical, warning, resolved_today }
GET   /api/v1/alerts/stats          # { total, active, resolved, critical, warning }
POST  /api/v1/alerts/{id}/acknowledge   # active -> acknowledged (devops/admin only)
POST  /api/v1/alerts/{id}/resolve        # -> resolved (devops/admin only)
```

**Incidents** are now modeled separately from alerts — an Alert is a raw
signal, an Incident is what a human actually tracks to resolution. Incidents
can be created directly or promoted from an existing alert:

```
GET   /api/v1/incidents?status=open
GET   /api/v1/incidents/{id}
POST  /api/v1/incidents                       # create directly (devops/admin)
POST  /api/v1/incidents/from-alert/{alert_id}  # promote an alert (idempotent)
PATCH /api/v1/incidents/{id}                    # open -> acknowledged -> resolved
```

Migration `0003` adds `alerts.status`, `alerts.acknowledged_by`, and
`incidents.alert_id`. `alerts.resolved` (bool) is kept in sync with
`status == "resolved"` so nothing that reads the old field breaks.

The Alerts page in the frontend now shows a dashboard summary strip and
Acknowledge/Resolve buttons (visible to `admin`/`devops_engineer` roles).
