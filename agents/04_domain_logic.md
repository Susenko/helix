# Domain Logic & Integrations

## Google Integration
HELIX tightly integrates with Google Services, specifically Calendar.

### OAuth Flow
1. **Initiation**: User starts OAuth flow via `/oauth/google/start` (in Core).
2. **Storage**: Access and Refresh tokens are stored in the `google_oauth_tokens` table in Postgres.
3. **Refreshes**: The system automatically checks token expiry before making API calls and refreshes access tokens using `apps/core/app/domain/services/google_oauth.py`.

### Calendar Operations
- **Listing Events**: Retrieves calendar events for the current day or specified range.
- **Free Slots**: The system includes a service `free_slots.py` that analyzes calendar events to find gaps in the schedule, presumably for booking or suggestion purposes.

## Realtime Features
- **Voice/Agent**: The presence of `realtime.py` in core and `@openai/agents` in web suggests a voice-enabled or realtime chat interface powered by OpenAI.
- **Client Secrets**: Ephemeral tokens are generated on the backend (`create_client_secret`) to allow the frontend to connect securely to the realtime API.

## Data Models
- **Tensions**: A core concept in the system. Likely represents "problems", "issues", or "topics" the user wants to address.
- **Baseline Fields**: Configuration or profile data associated with the user/system state.
