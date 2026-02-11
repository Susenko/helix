# Backend Architecture (Core)

## Overview
The backend is a Python application using **FastAPI**. It is located in `apps/core`.

## Structure
- **Entry Point**: `app/main.py` - Sets up the FastAPI app, CORS middleware, and mounts routers.
- **Configuration**: `app/settings.py` - Manages environment variables and app settings.

## Database Layer
- **ORM**: SQLAlchemy (Async)
- **Migrations**: Alembic (`alembic/` folder)
- **Session**: `app/infra/db/session.py` - Handles database connections.
- **Models**: Located in `app/infra/db/models/`. Major entities include:
  - `GoogleOAuthToken`: Stores tokens for Google integrations.
  - `Tension`, `TensionEvent`: Domain entities for tracking user states/issues.
  - `BaselineField`: Configuration fields.

## API Structure
Routers are located in `app/api/routers/`.
- **Calendar (`/calendar`)**: Handles Google Calendar operations (list events, find free slots).
- **OAuth (`/oauth`)**: Manages Google OAuth 2.0 flow for authentication.
- **Tensions (`/tensions`)**: Create/list/update tension containers (`POST /tensions`, `GET /tensions/active`, `PATCH /tensions/{id}`).
- **Baseline Fields (`/baseline-fields`)**: CRUD for background domains (`POST /baseline-fields`, `GET /baseline-fields`, `PATCH /baseline-fields/{id}`, `DELETE /baseline-fields/{id}`).
- **Realtime**: dedicated endpoints for realtime voice/data connections.

## Domain Services
Business logic is encapsulated in `app/domain/services/`.
- **`google_calendar.py`**: Wrapper for Google Calendar API (list events, create events).
- **`google_oauth.py`**: Handles token management, refresh flows.
- **`free_slots.py`**: Logic to calculate available time slots based on calendar data.
