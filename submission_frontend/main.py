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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("submission_frontend")

# Import calculate_plant_moisture locally or fallback to botanical watering skill scripts path
try:
    from moisture_calculator import calculate_plant_moisture
    logger.info("Successfully imported calculate_plant_moisture locally.")
except ImportError:
    base_project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    skill_scripts_dir = os.path.join(base_project_dir, "skills", "botanical-watering-skill", "scripts")
    if skill_scripts_dir not in sys.path:
        sys.path.append(skill_scripts_dir)
    try:
        from moisture_calculator import calculate_plant_moisture
        logger.info("Successfully imported calculate_plant_moisture from Botanical Watering Skill.")
    except Exception as e:
        logger.error(f"Failed to import calculate_plant_moisture: {e}")

# Initialize Vertex AI SDK
import vertexai
from vertexai import agent_engines

app = FastAPI(title="FloraWave Presentation Dashboard", version="0.1.0")

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
    country: str,
    plant_name: str,
    species: str,
    last_watered: str,
    sun_hours: float,
    is_covered: bool
):
    """Sends plant data to the deployed Agent Runtime and parses the recommendation."""
    if not agent_engine:
        raise HTTPException(status_code=500, detail="Vertex AI Agent Engine is not initialized.")
        
    # 1. Geocode location to get latitude and longitude
    lat, lon = 48.13743, 11.57549  # Default to Munich
    try:
        geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city},{country}&count=1&format=json"
        async with httpx.AsyncClient() as client:
            geo_res = await client.get(geocode_url)
            geo_res.raise_for_status()
            geo_data = geo_res.json()
            if "results" in geo_data and len(geo_data["results"]) > 0:
                result = geo_data["results"][0]
                lat = result["latitude"]
                lon = result["longitude"]
    except Exception as e:
        logger.error(f"Geocoding failed, using fallback coordinates. Error: {e}")
        
    # 2. Calculate days since last watered
    now = datetime.datetime.now(datetime.timezone.utc)
    try:
        last_watered_dt = datetime.datetime.fromisoformat(last_watered.replace("Z", "+00:00"))
    except Exception as e:
        logger.error(f"Failed to parse last_watered: {last_watered}. Error: {e}")
        last_watered_dt = now - datetime.timedelta(days=2)
        
    days_since = (now - last_watered_dt).days
    days_since = max(0, min(30, days_since))
    
    # 3. Fetch hourly historical weather data and group by day
    weather_data = {
        "time": [],
        "temperature_mean_c": [],
        "humidity_mean_percent": [],
        "precipitation_sum_mm": []
    }
    
    try:
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&hourly=temperature_2m,relative_humidity_2m,precipitation"
            f"&timezone=auto&past_days={days_since}&forecast_days=1"
        )
        async with httpx.AsyncClient() as client:
            res = await client.get(weather_url)
            res.raise_for_status()
            res_json = res.json()
            
            if "hourly" in res_json:
                hourly = res_json["hourly"]
                times = hourly.get("time", [])
                temps = hourly.get("temperature_2m", [])
                humidities = hourly.get("relative_humidity_2m", [])
                precips = hourly.get("precipitation", [])
                
                # Group hourly data by date (YYYY-MM-DD)
                daily_groups = {}
                for idx, t_str in enumerate(times):
                    date_key = t_str.split("T")[0]
                    if date_key not in daily_groups:
                        daily_groups[date_key] = {"temps": [], "humidities": [], "precips": []}
                    
                    if idx < len(temps) and temps[idx] is not None:
                        daily_groups[date_key]["temps"].append(temps[idx])
                    if idx < len(humidities) and humidities[idx] is not None:
                        daily_groups[date_key]["humidities"].append(humidities[idx])
                    if idx < len(precips) and precips[idx] is not None:
                        daily_groups[date_key]["precips"].append(precips[idx])
                
                sorted_dates = sorted(daily_groups.keys())
                for date in sorted_dates:
                    group = daily_groups[date]
                    avg_temp = sum(group["temps"]) / len(group["temps"]) if group["temps"] else 20.0
                    avg_hum = sum(group["humidities"]) / len(group["humidities"]) if group["humidities"] else 60.0
                    sum_prec = sum(group["precips"]) if group["precips"] else 0.0
                    
                    weather_data["time"].append(date)
                    weather_data["temperature_mean_c"].append(round(avg_temp, 2))
                    weather_data["humidity_mean_percent"].append(round(avg_hum, 2))
                    weather_data["precipitation_sum_mm"].append(round(sum_prec, 2))
                
                logger.info(f"Processed daily weather data: {len(weather_data['time'])} days.")
    except Exception as e:
        logger.error(f"Error fetching/processing historical weather hourly: {e}")
        # Build fallback mock weather arrays
        dates = [(now - datetime.timedelta(days=d)).strftime("%Y-%m-%d") for d in range(days_since + 1)]
        dates.reverse()
        weather_data["time"] = dates
        weather_data["temperature_mean_c"] = [20.0] * len(dates)
        weather_data["humidity_mean_percent"] = [60.0] * len(dates)
        weather_data["precipitation_sum_mm"] = [0.0] * len(dates)
        
    # 4. Calculate plant moisture using the Skill script
    moisture_level = 50
    status = "Healthy"
    next_watering_date = (now + datetime.timedelta(days=2)).strftime("%Y-%m-%d")
    
    try:
        balcony_config = {
            "city": city,
            "country": country,
            "isCovered": is_covered,
            "defaultSunHours": sun_hours
        }
        plant_dict = {
            "id": "temp-plant-id",
            "species": species,
            "lastWatered": last_watered,
            "sunHours": sun_hours
        }
        calc_res = calculate_plant_moisture(plant_dict, balcony_config, weather_data)
        moisture_level = calc_res.get("moisture_level", 50)
        status = calc_res.get("status", "Healthy")
        next_watering_date = calc_res.get("next_watering_date", next_watering_date)
        logger.info(f"Skill calculation complete: moisture_level={moisture_level}%, status={status}, next_watering_date={next_watering_date}")
    except Exception as e:
        logger.error(f"Failed to calculate plant moisture via skill: {e}")

    # Build weather summary to describe in prompt
    avg_temp_recent = sum(weather_data["temperature_mean_c"]) / len(weather_data["temperature_mean_c"]) if weather_data["temperature_mean_c"] else 20.0
    sum_rain_recent = sum(weather_data["precipitation_sum_mm"])
    weather_summary = f"Mean temp: {round(avg_temp_recent, 1)}°C, Total rain: {round(sum_rain_recent, 1)}mm"
    
    # 5. Format prompt to obtain the English explanation from the Agent
    prompt = f"""
    You are the FloraWave Botanical Assistant. Provide a 1-2 sentence English explanation for the watering recommendation of this plant:
    - Plant Name: {plant_name}
    - Species/Category: {species}
    - Calculated Soil Moisture: {moisture_level}%
    - Recommended Status: {status}
    - Next Watering Date: {next_watering_date}
    - Location: {city}, {country}
    - Balcony Type: {"Covered" if is_covered else "Open"}
    - Actual Daily Sun Hours: {sun_hours}
    - Recent Weather Summary: {weather_summary}
    
    Please follow these rules from the Botanical Watering Skill:
    - Cite the calculated moisture level ({moisture_level}%).
    - Cite the location and recent weather conditions (e.g. mean temperature {round(avg_temp_recent, 1)}°C, total rain {round(sum_rain_recent, 1)}mm).
    - Cite if the actual daily sun hours ({sun_hours} hrs/day) deviate from the optimal sun hours for this plant category.
    - Cite if the balcony type ({ "covered" if is_covered else "open" }) and rain had an impact.

    Return your output STRICTLY as a JSON object with the following keys (no markdown wrapping, no extra text, just raw JSON):
    {{
      "moisture_level": {moisture_level},
      "status": "{status}",
      "next_watering_date": "{next_watering_date}",
      "explanation": "<your 1-2 sentence English explanation>"
    }}
    """
    
    try:
        # Create a new session
        session = await agent_engine.async_create_session(user_id="default-user")
        sess_uuid = session["id"]
        
        logger.info(f"Querying deployed agent with async_stream_query...")
        response = agent_engine.async_stream_query(
            session_id=sess_uuid,
            message=prompt,
            user_id="default-user"
        )
        
        # Parse the response text from streamed chunks
        response_text = ""
        async for chunk in response:
            if hasattr(chunk, 'content') and chunk.content:
                for part in chunk.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_text += part.text
            elif isinstance(chunk, dict):
                content = chunk.get("content", {})
                if isinstance(content, dict):
                    parts = content.get("parts", [])
                    for part in parts:
                        if "text" in part:
                            response_text += part["text"]
                elif isinstance(content, str):
                    response_text += content
        
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

# Mount img files
img_dir = os.path.join(os.path.dirname(__file__), "img")
if os.path.exists(img_dir):
    app.mount("/img", StaticFiles(directory=img_dir), name="img")

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
else:
    @app.get("/")
    def read_root():
        return {"message": "FloraWave Presentation Dashboard is running. Build static folder to view frontend."}

if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8001))
    reload = True if host == "127.0.0.1" else False
    uvicorn.run("main:app", host=host, port=port, reload=reload)
