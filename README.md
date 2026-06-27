# FloraWave: Premium AI Plant Advisor 🌿🌊

FloraWave is an AI-powered concierge agent and dashboard designed to help balcony gardeners maintain optimal plant health through advanced soil moisture depletion simulations and real-time weather analytics. It integrates physical mathematical models of evapotranspiration with Google Cloud's Vertex AI Agent Runtime (Reasoning Engine) to deliver highly personalized, mathematically consistent, and natural language watering recommendations in German.

## 🚀 Key Features

* **Soil Moisture Depletion Simulation:** Uses a deterministic mathematical model based on plant species categories (Mediterranean herbs, water-loving flowers, succulents, etc.) to simulate daily moisture loss.
* **Real Historical Weather Integration:** Automatically fetches actual daily weather records (mean temperature, relative humidity, and precipitation sums) via the **Open-Meteo API** for the exact days since the plant was last watered, rather than relying on generative AI "guesses".
* **Vertex AI Reasoning Engine Integration:** Translates raw physical simulation data and balcony settings (sun exposure hours, whether the balcony is covered) into a structured German explanation using the `gemini-2.5-flash` model.
* **Local Image Uploads (Base64 Cache):** Allows users to upload plant images directly from their computer. The application uses a canvas-based compression and resizing pipeline to limit storage impact and cache images inside the browser's `localStorage`.
* **Flexible Image Sources:** Supports both absolute web URLs and relative paths (e.g. `/img/App_Logo.svg` for default plants) thanks to modified input field validation rules.
* **Pre-commit Security Checks:** A built-in git-commit helper skill checks all staged changes for absolute system paths, exposed API keys, and accidentally tracked `.env` files before committing.

---

## 🏗️ Project Architecture

```
_Capstone_Project/
├── submission_frontend/         # FastAPI web server and FloraWave UI (HTML/CSS/JS)
│   ├── static/                  # Static frontend files (index.html, style.css, img/)
│   ├── main.py                  # FastAPI server endpoints & Vertex AI reasoning client
│   ├── moisture_calculator.py   # Evapotranspiration simulation logic
│   └── plant_database.json      # Plant category rules & baseline depletion values
│
├── floracast-agent/             # Vertex AI Agent Runtime codebase (Reasoning Engine)
│   ├── app/                     # Core ReAct agent definition using Google ADK
│   │   ├── agent.py             # Agent definitions & tool bindings
│   │   └── agent_runtime_app.py # Reasoning Engine app initialization
│   └── pyproject.toml           # Agent dependencies
│
├── skills/                      # Custom developer/agent skills
│   ├── botanical-watering-skill # Contains the master watering skill & calculations
│   └── git-commit-version       # Contains git safety hooks & pre-commit validation
│
├── mcp_server/                  # Model Context Protocol (MCP) server
│   └── weather_mcp.py           # Weather tool provider
│
└── docs/                        # Conversation logs and design documentations
```

---

## 🛠️ Local Development & Setup

### Prerequisites

1. **Python 3.11+**
2. **uv** (Astral's fast Python package manager)
3. **Google Cloud SDK** (authenticated with project rights)
4. **Active Vertex AI Reasoning Engine** (already deployed on GCP)

### 1. Environment Configuration

For local development using the standard Gemini backend, create a `.env` file in the project root (based on `.env.example`) and add your Gemini API Key:

```env
GEMINI_API_KEY="your_gemini_api_key_here"
```

### 1.1 Coupling with Your Own Google Cloud Project

To connect this application to your own Google Cloud infrastructure and Vertex AI reasoning engine, you do **not** need to add GCP variables to your local `.env`. Instead, configure them using one of the following methods:

* **Production Frontend ([submission_frontend/main.py](submission_frontend/main.py)):**
  The FastAPI server in `submission_frontend/main.py` (lines 49-51) contains fallback default strings for project configurations. To couple the app with your GCP project:
  * **Option A (Code Edit):** Modify the fallback default values directly in `submission_frontend/main.py` (lines 49-51) with your project-specific details:
    * `PROJECT_ID`: Your GCP Project ID.
    * `LOCATION`: The GCP Region (e.g., `us-east1`).
    * `AGENT_RUNTIME_ID`: The resource name of your deployed reasoning engine.
  * **Option B (Deployment Configuration):** Pass them as environment variables during your Cloud Run deployment (using `--set-env-vars="GOOGLE_CLOUD_PROJECT=...,AGENT_RUNTIME_ID=..."` as shown in the deployment section below).

* **Reasoning Engine Agent ([floracast-agent/app/agent.py](floracast-agent/app/agent.py)):**
  If you are deploying your own agent via `agents-cli`, the default project and location fallbacks are set in `floracast-agent/app/agent.py` (lines 33-35). Ensure they match your target GCP project configuration.

* **Local Development Backend ([backend/main.py](backend/main.py)):**
  The local FastAPI backend server (which uses standard Gemini models from AI Studio rather than the deployed GCP Reasoning Engine) only requires the `GEMINI_API_KEY` in your local `.env` file. It verifies this key in `backend/main.py` (lines 47-52).

### 2. Running the Presentation Frontend Locally

Navigate to the `submission_frontend` folder, install dependencies, and start the local FastAPI web server:

```powershell
cd submission_frontend
uv run uvicorn main:app --port 8001 --reload
```

Open your browser and navigate to:
👉 **`http://localhost:8001`**

### 3. Running the Agent Playground Locally

If you want to test and query the ReAct agent locally in a chat shell:

```powershell
cd floracast-agent
uvx google-agents-cli setup
agents-cli install
agents-cli playground
```

---

## 🚀 Cloud Run Deployment

To deploy the presentation frontend to Google Cloud Run, run the deployment command (using your local `gcloud` SDK):

```powershell
$token = (python -c "import google.auth, google.auth.transport.requests; creds, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform']); creds.refresh(google.auth.transport.requests.Request()); print(creds.token)")
$env:CLOUDSDK_AUTH_ACCESS_TOKEN = $token

gcloud run deploy garden-organizer-dashboard `
  --source=submission_frontend `
  --project=<YOUR_GCP_PROJECT_ID> `
  --region=<YOUR_GCP_REGION> `
  --set-env-vars="GOOGLE_CLOUD_PROJECT=<YOUR_GCP_PROJECT_ID>,AGENT_RUNTIME_ID=projects/<YOUR_GCP_PROJECT_NUMBER>/locations/<YOUR_GCP_REGION>/reasoningEngines/<YOUR_REASONING_ENGINE_ID>" `
  --allow-unauthenticated `
  --quiet
```

### Granting Service Account IAM Permissions

After deployment, grant the dashboard's default runtime service account (Compute Engine default) the Vertex AI User role so it can query the reasoning engine:

```powershell
gcloud projects add-iam-policy-binding <YOUR_GCP_PROJECT_ID> `
  --member="serviceAccount:<YOUR_GCP_PROJECT_NUMBER>-compute@developer.gserviceaccount.com" `
  --role="roles/aiplatform.user" `
  --quiet
```

---

## 🔒 Security & Git Commit Safety

To ensure no environment files (`.env`), system absolute paths, or private API keys are accidentally committed to the public Git repository, use the `git-commit-version` skill to commit your changes:

```powershell
python skills/git-commit-version/scripts/safe_commit.py "your commit message here"
```

The script automatically:
1. Assures `.env` is ignored and not tracked.
2. Checks all staged changes for hardcoded credentials (e.g. `GEMINI_API_KEY`).
3. Checks for absolute system paths containing user profile directories.
4. Executes the commit only if all safety checks pass.
