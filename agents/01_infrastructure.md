# Infrastructure & Deployment

## Overview
The HELIX project uses Docker Compose to orchestrate its services. The system is containerized to ensure consistent environments across development and production.

## Services

### 1. Helix Core (`helix-core`)
- **Path**: `apps/core`
- **Port**: `8000`
- **Description**: The main backend service built with FastAPI. It handles API requests, database interactions, and business logic.
- **Dependencies**: `postgres`, `redis`

### 2. Helix Web (`helix-web`)
- **Path**: `apps/web`
- **Port**: `3000`
- **Description**: The frontend interface built with Next.js 15. Provides the user interface for interacting with Helix agents and tools.
- **Dependencies**: `helix-core` (for API calls)

### 3. Postgres (`postgres`)
- **Image**: `postgres:16`
- **Port**: `5432`
- **Description**: Primary relational database for storing user data, settings, and application state.
- **Volume**: `pgdata`

### 4. Redis (`redis`)
- **Image**: `redis:7`
- **Port**: `6379`
- **Description**: In-memory data store, likely used for caching or task queues (if implemented).

### 5. PgAdmin (`pgadmin`)
- **Image**: `dpage/pgadmin4:latest`
- **Port**: `8080`
- **Description**: Web-based administration tool for PostgreSQL.
- **Credentials**: configured in `compose.yml` (default: `admin@helix.com` / `secret123`)

## Network
Internal communication happens via the default Docker bridge network. 
- `helix-web` communicates with `helix-core` via the service name `helix-core:8000`.

## Environment Variables
Configuration is managed via a `.env` file in the root directory, passed to containers via `env_file`.
Key variables:
- `HELIX_ALLOWED_ORIGIN`: CORS settings for the backend.
- `OPENAI_API_KEY`: API key for AI features.
- `NEXT_PUBLIC_CORE_URL`: Public URL for the backend API.
