Vibe-code a standalone FloraCast dashboard service in a new folder
"submission_frontend/". I want:

  - A FastAPI service with the following endpoints:
    1. GET /: Serves a beautiful, interactive plant-care dashboard HTML page. Use the frontend in `frontend/` as a design template (dark glassmorphism theme, Inter/Outfit fonts, green accent palette). Convert all text into English. Display all units in both European and American standard (e.g., temperatures in °C and °F, distances in km and mi).
    2. GET /api/analyze: Accepts query parameters for city, plant name, species, last watered date, sun hours, and whether the balcony is covered. Sends these as a structured prompt to the deployed FloraCast Agent Runtime (via the Vertex AI `agent_engines` SDK). Returns the agent's watering recommendation including moisture level, status (Healthy/Water Soon/Water Now), next watering date, and a natural-language explanation.
    3. GET /api/weather/{city}: Queries the Open-Meteo API (same logic as `mcp_server/weather_mcp.py`) to fetch current weather data (temperature, humidity, precipitation) for a given city. Returns the data with dual-unit formatting.
    4. GET /api/sessions: Lists recent agent sessions from the Agent Runtime via the `agent_engines` SDK, showing session ID, timestamp, and the last agent response summary. This demonstrates the ADK session management capability.

  - Read the following from environment variables:
    - GOOGLE_CLOUD_PROJECT (GCP project ID, e.g., "capstonewaterplantsproject")
    - AGENT_RUNTIME_ID (the deployed Reasoning Engine resource name, e.g., "projects/882498418292/locations/us-east1/reasoningEngines/9003645633160019968")
    - GOOGLE_CLOUD_LOCATION (e.g., "us-east1")

  - A pyproject.toml with fastapi, uvicorn, google-adk, google-cloud-aiplatform, requests, and python-dotenv.

  - The dashboard UI should include:
    1. A hero section with the FloraCast logo/title and a brief tagline about AI-powered plant care.
    2. A plant analysis form where users can input plant details (name, species dropdown with categories from the botanical-watering-skill, last watered date, sun hours, city, balcony covered toggle). On submit, it calls GET /api/analyze and displays the result in an animated card.
    3. A live weather widget showing the current conditions for the configured city (from GET /api/weather), with temperature in both °C/°F and humidity percentage.
    4. A session history panel that lists recent agent interactions (from GET /api/sessions), with expandable rows to see full conversation details.
    5. Status indicators using the project's color scheme: green (#10b981) for Healthy, amber (#f59e0b) for Water Soon, red (#ef4444) for Water Now.

Make sure the UI looks highly polished and premium (glassmorphism cards, smooth transitions, loading spinners during API calls, responsive layout, and micro-animations on hover/interaction). The design should match the existing frontend's dark-mode aesthetic. Show me the main.py implementation when done.