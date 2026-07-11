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

## What's next

Phase 2 (Observability Layer) connects Prometheus, Node Exporter,
kube-state-metrics, and the Kubernetes API so the **Monitoring** page starts
showing live data instead of the "ships in Phase 2" placeholder.
