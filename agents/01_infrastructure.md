# Infrastructure & Deployment

## Overview
The HELIX project uses Docker Compose to orchestrate its services. The system is containerized to ensure consistent environments across development and production.
There are two compose profiles:
- `docker/compose.yml`: development stack (includes PgAdmin).
- `docker/compose-prod.yml`: production stack (without PgAdmin).

## Services

### 1. Helix Core (`helix-core`)
- **Path**: `apps/core`
- **Container name**: `helix-core`
- **Port**: `8000`
- **Description**: The main backend service built with FastAPI. It handles API requests, database interactions, and business logic.
- **Dependencies**: `postgres`, `redis`

### 2. Helix Web (`helix-web`)
- **Path**: `apps/web`
- **Container name**: `helix-web`
- **Port**: host `3006` -> container `3000`
- **Description**: The frontend interface built with Next.js 15. Provides the user interface for interacting with Helix agents and tools.
- **Dependencies**: `helix-core` (for API calls)
- **Prod runtime**: `docker/compose-prod.yml` uses `apps/web/Dockerfile.prod`, which runs `npm run build` during image build and starts with `npm run start`.

### 3. Postgres (`postgres`)
- **Image**: `postgres:16`
- **Container name**: `helix-postgres`
- **Port**: dev `5432`, prod internal-only (no host publish)
- **Description**: Primary relational database for storing user data, settings, and application state.
- **Volume**: `pgdata`

### 4. Redis (`redis`)
- **Image**: `redis:7`
- **Container name**: `helix-redis`
- **Port**: dev `6379`, prod internal-only (no host publish)
- **Description**: In-memory data store, likely used for caching or task queues (if implemented).

### 5. PgAdmin (`pgadmin`)
- **Image**: `dpage/pgadmin4:latest`
- **Container name**: `helix-pgadmin`
- **Port**: `8080`
- **Description**: Web-based administration tool for PostgreSQL.
- **Credentials**: configured in `compose.yml` (default values in repo).
- **Availability**: development compose only.

## Network
Internal communication happens via the default Docker bridge network. 
- `helix-web` communicates with `helix-core` via the service name `helix-core:8000`.
- `helix-web` is additionally attached to external Docker network `shared-net` for host/service sharing with other stacks.
- `shared-net` must exist before `compose up`:
  `docker network create shared-net` (one-time).

## Environment Variables
Configuration is managed via a `.env` file in the root directory, passed to containers via `env_file`.
Key variables:
- `HELIX_ALLOWED_ORIGIN`: CORS settings for the backend (should match frontend host, now `http://localhost:3006`).
- `OPENAI_API_KEY`: API key for AI features.
- `NEXT_PUBLIC_CORE_URL`: Public URL for the backend API.
- `NEXT_PUBLIC_CORE_HTTP_URL`: Browser-facing backend URL for client-side fetch requests in web app.

## Deployment Helper
- `deploy/deploy.sh` syncs the repository to a remote host and runs:
  `docker compose -f docker/compose-prod.yml --env-file .env up -d --build`
- Usage: `./deploy/deploy.sh <user@host> [remote_path]`
