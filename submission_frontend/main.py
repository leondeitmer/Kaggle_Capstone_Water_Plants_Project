import os
import sys
import datetime
import json
import logging
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import httpx
from dotenv import load_dotenv

# Load local env file
load_dotenv()

# Initialize Vertex AI SDK
import vertexai
from vertexai import agent_engines

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("submission_frontend")

app = FastAPI(title="FloraCast Presentation Dashboard", version="0.1.0")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "capstonewaterplantsproject")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-east1")
AGENT_RUNTIME_ID = os.environ.get("AGENT_RUNTIME_ID", "projects/882498418292/locations/us-east1/reasoningEngines/9003645633160019968")

# In-memory session tracking
SESSIONS_DB = []

try:
    logger.info(f"Initializing Vertex AI with project={PROJECT_ID}, location={LOCATION}")
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    logger.info(f"Loading deployed Agent Engine: {AGENT_RUNTIME_ID}")
    agent_engine = agent_engines.get(AGENT_RUNTIME_ID)
    logger.info("Agent Engine loaded successfully.")
except Exception as e:
    logger.error(f"Failed to initialize Vertex AI Agent Engine: {e}")
    agent_engine = None

GEO_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

@app.get("/api/weather/{city}")
async def get_weather(city: str):
    """Fetch current weather for a city with dual-unit formatting."""
    try:
        async with httpx.AsyncClient() as client:
            # 1. Geocode location
            geo_res = await client.get(GEO_API_URL, params={"name": city, "count": 1, "format": "json"}, timeout=10.0)
            geo_res.raise_for_status()
            geo_data = geo_res.json()
            
            if "results" not in geo_data or not geo_data["results"]:
                raise HTTPException(status_code=404, detail=f"City '{city}' not found.")
            
            result = geo_data["results"][0]
            lat = result["latitude"]
            lon = result["longitude"]
            display_name = f"{result['name']}, {result.get('country', '')}"
            
            # 2. Fetch current weather
            weather_params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,precipitation",
                "timezone": "auto"
            }
            weather_res = await client.get(OPEN_METEO_URL, params=weather_params, timeout=10.0)
            weather_res.raise_for_status()
            weather_data = weather_res.json()
            
            if "current" not in weather_data:
                raise HTTPException(status_code=500, detail="Invalid weather data structure.")
            
            current = weather_data["current"]
            temp_c = current["temperature_2m"]
            temp_f = (temp_c * 9/5) + 32
            
            precip_mm = current["precipitation"]
            precip_in = precip_mm * 0.03937
            
            humidity = current["relative_humidity_2m"]
            
            return {
                "city": display_name,
                "latitude": lat,
                "longitude": lon,
                "temp_c": round(temp_c, 1),
                "temp_f": round(temp_f, 1),
                "humidity": humidity,
                "precipitation_mm": round(precip_mm, 2),
                "precipitation_in": round(precip_in, 2)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather retrieval failed: {str(e)}")

@app.get("/api/analyze")
async def analyze_plant(
    city: str,
    plant_name: str,
    species: str,
    last_watered: str,
    sun_hours: float,
    is_covered: bool
):
    """Sends plant data to the deployed Agent Runtime and parses the recommendation."""
    if not agent_engine:
        raise HTTPException(status_code=500, detail="Vertex AI Agent Engine is not initialized.")
    
    # Format a structured prompt for the agent
    prompt = f"""
    You are the FloraCast Botanical Assistant. Analyze the following plant and provide a watering recommendation:
    - Plant Name: {plant_name}
    - Species/Category: {species}
    - Last Watered: {last_watered}
    - Sun Hours/Day: {sun_hours}
    - Balcony Type: {"Covered" if is_covered else "Open"}
    - Location: {city}

    First, check the weather in {city} using your get_weather tool.
    Then, calculate the estimated moisture level (0-100%) and determine the watering status:
    - "Healthy": Moisture >= 50%
    - "Water Soon": Moisture 25-49%
    - "Water Now": Moisture < 25%

    Return your output STRICTLY as a JSON object with the following keys (no markdown wrapping, no extra text, just raw JSON):
    {{
      "moisture_level": <integer_0_to_100>,
      "status": "Healthy" | "Water Soon" | "Water Now",
      "next_watering_date": "YYYY-MM-DD",
      "explanation": "<1-2 sentence explanation in English citing the weather and sun exposure>"
    }}
    """
    
    try:
        # Create a new session
        session_id = f"sess-{int(datetime.datetime.now().timestamp())}"
        logger.info(f"Creating session: {session_id} for user default-user")
        
        session = agent_engine.create_session(user_id="default-user")
        sess_uuid = session["id"]
        
        logger.info(f"Querying deployed agent with prompt...")
        response = agent_engine.query(
            session_id=sess_uuid,
            message=prompt,
            user_id="default-user"
        )
        
        # Parse the response text
        response_text = ""
        if hasattr(response, 'content') and response.content:
            for part in response.content.parts:
                if hasattr(part, 'text') and part.text:
                    response_text += part.text
        elif isinstance(response, dict):
            content = response.get("content", {})
            if isinstance(content, dict):
                parts = content.get("parts", [])
                for part in parts:
                    if "text" in part:
                        response_text += part["text"]
            elif isinstance(content, str):
                response_text = content
        
        logger.info(f"Raw agent response: {response_text}")
        
        # Extract JSON from response (handling potential markdown formatting)
        json_str = response_text.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        json_str = json_str.strip()
        
        result_data = json.loads(json_str)
        
        # Save session info to our local DB
        session_info = {
            "session_id": sess_uuid,
            "timestamp": datetime.datetime.now().isoformat(),
            "plant_name": plant_name,
            "species": species,
            "status": result_data.get("status", "Unknown"),
            "moisture_level": result_data.get("moisture_level", 0),
            "explanation": result_data.get("explanation", "")
        }
        SESSIONS_DB.append(session_info)
        
        return {
            "session_id": sess_uuid,
            "analysis": result_data
        }
        
    except Exception as e:
        logger.error(f"Agent query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Agent analysis failed: {str(e)}")

@app.get("/api/sessions")
async def get_sessions():
    """List recent agent sessions and summaries."""
    return SESSIONS_DB

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
else:
    @app.get("/")
    def read_root():
        return {"message": "FloraCast Presentation Dashboard is running. Build static folder to view frontend."}

if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8001))
    reload = True if host == "127.0.0.1" else False
    uvicorn.run("main:app", host=host, port=port, reload=reload)
