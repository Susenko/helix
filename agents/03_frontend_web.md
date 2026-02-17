# Frontend Architecture (Web)

## Overview
The frontend is built with **Next.js 15** (using React 19) and TypeScript. It is located in `apps/web`.
In Docker, it runs as service/container `helix-web` on host port `3006` (container port `3000`).

## Key Technologies
- **Next.js App Router**: Uses the modern `/app` directory structure.
- **OpenAI Agents SDK**: `@openai/agents` is used, suggesting integration with OpenAI's realtime or agent capabilities.
- **Zod**: Used for schema validation.

## Structure
- **`app/page.tsx`**: Main entry point for the UI.
- **`app/api/`**: Next.js API Routes (BFF - Backend for Frontend pattern).
  - `helix/client-secret`: Proxies requests to get ephemeral keys for realtime sessions.
  - `helix/session`: Manages session state.

## Integration
The frontend communicates with `api/helix/*` routes which in turn communicate with the Core backend or external services like OpenAI.

## Current UI Capabilities
- Voice agent tools for calendar operations and tension management.
- Voice agent tools for baseline fields CRUD (`baseline_fields_list/create/update/delete`).
- Dashboard tables on `app/page.tsx` for active tensions and baseline fields, each with manual refresh buttons.

## Runtime Env Notes
- Browser-side calls from `app/page.tsx` use `NEXT_PUBLIC_CORE_HTTP_URL` (fallback: `NEXT_PUBLIC_CORE_URL`).
- BFF routes (`app/api/helix/*`) use `NEXT_PUBLIC_CORE_URL` for internal container-to-container access.
