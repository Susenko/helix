# HELIX Project Structure & Agents

## Project Overview

HELIX is a monorepo application integrating a FastAPI backend with a Next.js frontend, designed to work as an intelligent agent system with Google Calendar integration and Realtime capabilities.

## Detailed Documentation

The project structure is detailed in the following agent documentation files:

- **[Infrastructure](./agents/01_infrastructure.md)**: Docker setup, services, and networking.
- **[Backend Architecture](./agents/02_backend_core.md)**: Python/FastAPI core, database models, and API structure.
- **[Frontend Architecture](./agents/03_frontend_web.md)**: Next.js web application and OpenAI Agents SDK usage.
- **[Domain Logic](./agents/04_domain_logic.md)**: Business logic, Google OAuth/Calendar integration, and core concepts like "Tensions".

## Documentation Update Rule

If an agent makes structural or architectural changes (folders, services, modules, routes, integrations, environment variables, or workflows), the agent must update this `AGENTS.md` in the same task.

When relevant, the agent must also update corresponding detailed docs in `agents/*.md` so the high-level index and detailed pages stay consistent.

## Quick Start (Project Root)

The project is orchestrated via `docker/compose.yml`.

### Key Commands

- **Start System**: `docker compose -f docker/compose.yml up --build`
- **Stop System**: `docker compose -f docker/compose.yml down`
- **Backend API**: Accessible at `http://localhost:8000`
- **Frontend UI**: Accessible at `http://localhost:3006`
- **DB Admin**: Accessible at `http://localhost:8080`
- **Prod Compose**: `docker compose -f docker/compose-prod.yml up --build`
- **Deploy Script**: `./deploy/deploy.sh <user@host> [remote_path]`

## Service Map (Docker Compose)

- `helix-core`: FastAPI backend (`apps/core`), container `helix-core`, exposed on `:8000`, depends on `postgres` and `redis`.
- `helix-telegram-bot`: Telegram bot worker (`apps/core`, module `app.telegram_bot`), container `helix-telegram-bot`, runs long-polling with `TELEGRAM_BOT_TOKEN`, depends on `helix-core`.
- `helix-web`: Next.js frontend (`apps/web`), container `helix-web`, exposed on host `:3006` (container `:3000`), depends on `helix-core`.
  Production profile builds web via `apps/web/Dockerfile.prod` (`npm run build` + `npm run start`).
- `postgres`: PostgreSQL 16, container `helix-postgres` (dev: `:5432`, prod: internal-only) with volume `pgdata`.
- `redis`: Redis 7, container `helix-redis` (dev: `:6379`, prod: internal-only).
- `pgadmin`: PgAdmin 4, container `helix-pgadmin` (`:8080`) with volume `pgadmin_data` (dev compose only).

## Environment Variables (.env)

The root `.env` file is loaded by both `helix-core` and `helix-web` via Docker Compose.

### Core Required

- `OPENAI_API_KEY`: Used for OpenAI-powered features.
- `HELIX_ALLOWED_ORIGIN`: CORS allowed origin for backend.
- `DATABASE_URL`: SQLAlchemy async connection string for Postgres.
- `TELEGRAM_BOT_TOKEN`: Token for `helix-telegram-bot` (Telegram long-polling worker).

### Google Integration

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`

### Web Required

- `NEXT_PUBLIC_CORE_URL`: Backend base URL used by frontend/BFF routes.
- `NEXT_PUBLIC_CORE_HTTP_URL`: Public backend URL for browser-side requests from `app/page.tsx` (falls back to `NEXT_PUBLIC_CORE_URL`).
  In production this variable is passed both at runtime and as Docker build arg for Next.js client bundle.

## Development Workflows

### 1) Full stack via Docker (recommended)

- `docker compose -f docker/compose.yml up --build`
- Logs: `docker compose -f docker/compose.yml logs -f helix-core helix-web helix-telegram-bot`

### 1.1) Production profile (without PgAdmin)

- `docker compose -f docker/compose-prod.yml up --build`
- `docker compose -f docker/compose-prod.yml down`

### 1.2) Remote deploy helper

- `./deploy/deploy.sh <user@host> [remote_path]`
- Requires Docker + Compose plugin on server and `.env` in remote project path.

### 2) Web app only (inside `apps/web`)

- `npm run dev`
- Build check: `npm run build`

### 3) Core app and DB migrations (inside `apps/core`)

- Run API directly: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Run Telegram bot directly: `python -m app.telegram_bot`
- Apply migrations: `alembic upgrade head`
- Create migration: `alembic revision --autogenerate -m "message"`

## Where to Look First

- API entrypoint and router mounting: `apps/core/app/main.py`
- Telegram bot entrypoint: `apps/core/app/telegram_bot.py`
- Runtime settings/env parsing: `apps/core/app/settings.py`
- Domain services (OAuth/Calendar/free slots): `apps/core/app/domain/services/`
- Tensions API (`POST /tensions`, `GET /tensions/active`, `PATCH /tensions/{id}`): `apps/core/app/api/routers/tensions.py`
- Baseline Fields API (`POST /baseline-fields`, `GET /baseline-fields`, `PATCH /baseline-fields/{id}`, `DELETE /baseline-fields/{id}`): `apps/core/app/api/routers/baseline_fields.py`
- DB models: `apps/core/app/infra/db/models/`
- Frontend app root: `apps/web/app/page.tsx`
- Frontend BFF routes: `apps/web/app/api/helix/`

## Documentation Ownership Map

- Use `agents/01_infrastructure.md` for containers, networking, ports, and runtime topology.
- Use `agents/02_backend_core.md` for FastAPI layers, DB, routers, and backend internals.
- Use `agents/03_frontend_web.md` for App Router structure and frontend integration points.
- Use `agents/04_domain_logic.md` for Google OAuth/Calendar flow and domain concepts.

## Directory Structure

```
root/
├── apps/
│   ├── core/           # Backend (FastAPI, Alembic, SQLAlchemy)
│   └── web/            # Frontend (Next.js 15, React 19, Dockerfile.prod for prod build)
├── docker/
│   ├── compose.yml      # Dev Docker Compose definition (with PgAdmin)
│   └── compose-prod.yml # Prod Docker Compose definition (without PgAdmin)
├── deploy/             # Deploy helper scripts
├── manifests/          # Project principles and high-level docs
└── agents/             # Detailed system documentation (Auto-generated)
```
