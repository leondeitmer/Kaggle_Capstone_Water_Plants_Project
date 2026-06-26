# Conversation Log: Project Inception & Design Decisions

**Date:** June 26, 2026  
**Participants:** User & Antigravity (AI Coding Assistant)  
**Topic:** Initial planning, architecture, and requirements gathering for **FloraCast**.

---

## 1. Project Overview
The user initiated the project with the goal of building an AI-powered assistant for balcony plants to determine when they need watering. 

The core features requested:
1. Track balcony plants and record their last watered timestamps.
2. Build an AI Agent to calculate next watering needs on-demand.
3. Construct a trading-card-styled, scrollable frontend.
4. Host the application on Google Cloud and manage version control via GitHub.

---

## 2. Design Discussion & Revisions

### Weather Integration (Critique & Improvements)
*   **Original Idea:** Calculate water needs based on average temperatures since the last watering.
*   **Discussion:** The assistant recommended factoring in **humidity, sun exposure, and rain (precipitation)** since balcony plants are exposed to outdoor weather.
*   **Solution:** A custom Model Context Protocol (MCP) server will fetch historical weather and precipitation data from the Open-Meteo API. Open-Meteo is free and keyless, minimizing API security risks.
*   **Balcony Setup:** The user will input their City and Zip Code. The MCP server will automatically geocode these coordinates to retrieve weather data.
*   **Sun Hours:** A default sun hours setting is configured at the balcony level. Each plant inherits this default but can be customized (e.g., if placed in a shady corner).

### Database Decision (Security & Cost)
*   **Original Idea:** Connect to a secure database.
*   **Discussion:** Hosting a persistent database on Google Cloud for a small personal project can be complex and costly. Because Google Cloud Run is stateless, a local database file (like SQLite) would be wiped on every container sleep/restart.
*   **Solution (Option A):** Use the browser's `localStorage` to manage the plant state. The frontend handles all CRUD operations and stores the data locally. When an analysis is requested, the plant list and balcony config are sent to the stateless FastAPI backend. This ensures 100% user privacy, zero database maintenance, and zero database hosting costs.

### Plant Representation
*   Each plant card will feature an image link (`imageUrl`) provided by the user. If no URL is provided, a default placeholder leaf icon will be shown.

---

## 3. Agreed Architecture
*   **Frontend:** Vite (HTML, JS, Vanilla CSS) with `localStorage` database.
*   **Backend:** FastAPI (Python) implementing LangChain/Google GenAI agents.
*   **MCP Server:** Python MCP Server providing Geocoding and Weather History tools.
*   **Deployment:** Containerized unified deployment targeted for Google Cloud Run.
